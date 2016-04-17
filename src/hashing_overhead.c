#include <parc/algol/parc_SafeMemory.h>
#include <parc/algol/parc_BufferComposer.h>
#include <parc/algol/parc_LinkedList.h>
#include <parc/algol/parc_Iterator.h>

#include <parc/developer/parc_StopWatch.h>

#include <parc/security/parc_CryptoHasher.h>
#include <parc/security/parc_CryptoHashType.h>

#include <ccnx/common/ccnx_Name.h>
#include <ccnx/common/ccnx_NameSegment.h>

#include <stdio.h>
#include <ctype.h>

PARCBufferComposer *
readLine(FILE *fp)
{
    PARCBufferComposer *composer = parcBufferComposer_Create();
    char curr = fgetc(fp);
    while ((isalnum(curr) || curr == ':' || curr == '/' || curr == '.' ||
            curr == '_' || curr == '(' || curr == ')' || curr == '[' ||
            curr == ']' || curr == '-' || curr == '%' || curr == '+' ||
            curr == '=' || curr == ';' || curr == '$' || curr == '\'') && curr != EOF) {
        parcBufferComposer_PutChar(composer, curr);
        curr = fgetc(fp);
    }
    return composer;
}

void usage() {
    fprintf(stderr, "usage: hashing_overhead <uri_file>\n");
    fprintf(stderr, "   - uri_file: A file that contains a list of CCNx URIs -- one per line\n");
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        usage();
        exit(-1);
    }

    char *fname = argv[1];
    FILE *file = fopen(fname, "r");
    if (file == NULL) {
        perror("Could not open file");
        usage();
        exit(-1);
    }

    size_t num = 0;
    do {
        PARCBufferComposer *composer = readLine(file);
        PARCBuffer *bufferString = parcBufferComposer_ProduceBuffer(composer);
        if (parcBuffer_Remaining(bufferString) == 0) {
            break;
        }

        char *string = parcBuffer_ToString(bufferString);
        parcBufferComposer_Release(&composer);

        fprintf(stderr, "Read: %s\n", string);

        // Hash each name
        CCNxName *name = ccnxName_CreateFromCString(string);
        for (size_t i = 0; i < ccnxName_GetSegmentCount(name); i++) {
            PARCBufferComposer *composer = parcBufferComposer_Create();

            PARCStopwatch *timer = parcStopwatch_Create();
            parcStopwatch_Start(timer);

            uint64_t startBuildTime = parcStopwatch_ElapsedTimeNanos(timer);
            for (size_t j = 0; j <= i; j++) {
                CCNxNameSegment *segment = ccnxName_GetSegment(name, j);
                ccnxNameSegment_BuildString(segment, composer);
            }

            PARCBuffer *input = parcBufferComposer_ProduceBuffer(composer);
            uint64_t endBuildTime = parcStopwatch_ElapsedTimeNanos(timer);

            PARCCryptoHasher *digester = parcCryptoHasher_Create(PARC_HASH_SHA256);
            parcCryptoHasher_Init(digester);

            uint64_t startHashTime = parcStopwatch_ElapsedTimeNanos(timer);
            parcCryptoHasher_UpdateBuffer(digester, input);
            PARCCryptoHash *digestTest = parcCryptoHasher_Finalize(digester);
            uint64_t endHashTime = parcStopwatch_ElapsedTimeNanos(timer);

            uint64_t totalTime = (endHashTime - startHashTime) + (endBuildTime - startBuildTime);

            printf("%zu,%zu,%zu,%zu\n", num, i, parcBuffer_Remaining(input), totalTime);
        }

        num++;
    } while (true);

    return 0;
}
