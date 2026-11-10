#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "../antrag/api.h"
#include "../antrag/randombytes.h"
#include "cpucycles.h"
#include "speed_print.h"
#define CASES 100
#define RUNS 10001
extern prng p;
static secret_key sk;
static public_key pk;
static signature sig;
static uint8_t skb[ANTRAG_SK_SIZE], pkb[ANTRAG_PK_SIZE], sb[ANTRAG_SIG_SIZE];
static uint8_t msg[32];
static void require(int ok, const char *s) { if (!ok) { fprintf(stderr,"FAIL: %s\n",s); exit(1); } }
/* Initialize the repository PRNG, without changing its byte generation. */
static void seed(unsigned domain, unsigned index) {
    uint8_t b[8];
    for (int i=0;i<4;i++) { b[i]=(uint8_t)(domain>>(8*i)); b[i+4]=(uint8_t)(index>>(8*i)); }
    inner_shake256_context sc;
    inner_shake256_init(&sc); inner_shake256_inject(&sc,b,sizeof b);
    inner_shake256_flip(&sc); Zf(prng_init)(&p,&sc);
}
static unsigned attempts;
static void signed_bytes(void) {
    do { sign(sizeof msg,msg,&sk,&sig); attempts++; } while (encode_sig(sb,&sig));
}
static int verify_bytes(void) {
    decode_pk(&pk,pkb);
    if (decode_sig(&sig,sb)) return 0;
    return verify(sizeof msg,msg,&pk,&sig);
}
static void put(FILE *f,const void *v,size_t n) { require(fwrite(v,1,n,f)==n,"write"); }
static void get(FILE *f,void *v,size_t n) { require(fread(v,1,n,f)==n,"read"); }
static void vectors(const char *path,int check) {
    FILE *f=fopen(path,check?"rb":"wb"); require(f!=NULL,"vector file");
    for (unsigned i=0;i<CASES;i++) {
        for(unsigned j=0;j<sizeof msg;j++) msg[j]=(uint8_t)(i+j);
        if (!check) {
            seed(1,i); keygen_full(&sk,&pk); encode_sk(skb,&sk); encode_pk(pkb,&pk);
            decode_sk(&sk,skb); signed_bytes(); require(verify_bytes(),"self verification");
            put(f,pkb,sizeof pkb); put(f,skb,sizeof skb); put(f,sb,sizeof sb);
        } else {
            get(f,pkb,sizeof pkb); get(f,skb,sizeof skb); get(f,sb,sizeof sb);
            require(verify_bytes(),"cross verification");
            msg[0]^=1; require(!verify_bytes(),"reject changed message"); msg[0]^=1;
            /* Foreign serialized expanded keys must also sign interoperably. */
            decode_sk(&sk,skb); seed(2,i); signed_bytes();
            require(verify_bytes(),"foreign secret key");
        }
    }
    if(check) require(fgetc(f)==EOF,"trailing vector data");
    require(fclose(f)==0,"close"); printf("PASS %s 100 cases\n",check?"cross":"generate");
}
/* Parse all coefficient codewords. Zero bytes can be valid data. */
static size_t unpadded(void) {
    size_t bit=0;
    for(int i=0;i<ANTRAG_D;i++) {
        bit+=1+SIG_SMALL_BITS;
        for (;;) {
            require(bit < SIG_VECTOR_SIZE*8,"length parse bound");
            unsigned v=(sb[bit/8]>>(bit%8))&1; bit++; if(v) break;
        }
    }
    size_t used=(bit+7)/8;
    for(size_t i=used;i<SIG_VECTOR_SIZE;i++) require(sb[i]==0,"nonzero padding");
    /* Independent check from the decoded vector. */
    require(!decode_sig(&sig,sb),"length decode");
    size_t expected=0;
    for(int i=0;i<ANTRAG_D;i++) {
        int k=sig.s1.coeffs[i]; if(k>ANTRAG_Q/2) k-=ANTRAG_Q;
        unsigned a=(unsigned)(k<0?-k:k);
        expected+=SIG_SMALL_BITS+2+(a>>SIG_SMALL_BITS);
    }
    require((expected+7)/8==used,"length cross check");
    return used+SALT_BYTES;
}
static void lengths(void) {
    seed(4,0); keygen_full(&sk,&pk); attempts=0;
    unsigned long long total=0; size_t low=ANTRAG_SIG_SIZE,high=0;
    for(int i=0;i<10000;i++) {
        signed_bytes(); require(verify(sizeof msg,msg,&pk,&sig),"length verification");
        size_t n=unpadded(); total+=n; if(n<low)low=n; if(n>high)high=n;
    }
    printf("LENGTH %llu 10000 %zu %zu %u\n",total,low,high,attempts);
}
static void timing(void) {
    static uint64_t t[RUNS+1];
    seed(3,0); keygen_full(&sk,&pk); encode_pk(pkb,&pk); encode_sk(skb,&sk); signed_bytes();
    for(int op=0;op<4;op++) {
        unsigned verified=0;
        for(int i=0;i<RUNS;i++) {
            t[i]=cpucycles();
            if(op==0) { keygen_full(&sk,&pk); encode_pk(pkb,&pk); encode_sk(skb,&sk); }
            if(op==1) { decode_sk(&sk,skb); signed_bytes(); }
            if(op==2) { verified+=(unsigned)verify_bytes(); }
            if(op==3) { signed_bytes(); }
        }
        t[RUNS]=cpucycles();
        if(op==2) require(verified==RUNS,"timed verify");
        print_results((const char*[]){"KeyGen","Sign","Verify","ExpandedSign"}[op],t,RUNS+1);
        /* op0 changed the key; prepare a corresponding signature before verify. */
        if(op==0) signed_bytes();
    }
}
int main(int argc,char **argv) {
    require(argc>=2,"mode required");
    printf("META %d %d %d %d %d\n",ANTRAG_D,ANTRAG_Q,ANTRAG_PK_SIZE,ANTRAG_SK_SIZE,ANTRAG_SIG_SIZE);
    if(!strcmp(argv[1],"generate")||!strcmp(argv[1],"check")) { require(argc==3,"file required"); vectors(argv[2],!strcmp(argv[1],"check")); }
    else if(!strcmp(argv[1],"time")) timing();
    else if(!strcmp(argv[1],"length")) lengths();
    else require(0,"unknown mode");
    return 0;
}
