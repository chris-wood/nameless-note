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

static PARCBufferComposer *
_readLine(FILE *fp, PARCBufferComposer *composer)
{
    char curr = fgetc(fp);
    while ((isalnum(curr) || curr == ':' || curr == '/' || curr == '.' ||
            curr == '_' || curr == '(' || curr == ')' || curr == '[' ||
            curr == ']' || curr == '-' || curr == '%' || curr == '+' ||
            curr == '=' || curr == ';' || curr == '$' || curr == '\'') && curr != EOF) {

        if (curr == '%') {
            // pass
        } else if (curr == '=') {
            parcBufferComposer_PutChar(composer, '%');
            parcBufferComposer_PutChar(composer, '3');
            parcBufferComposer_PutChar(composer, 'D');
        } else {
            parcBufferComposer_PutChar(composer, curr);
        }

        curr = fgetc(fp);
    }

    return composer;
}

void usage() {
    fprintf(stderr, "usage: hashing_overhead <uri_file> <number of lines>\n");
    fprintf(stderr, "   - uri_file: A file that contains a list of CCNx URIs -- one per line\n");
    fprintf(stderr, "   - number of lines: The number of lines to process in the URI file\n");
}

int main(int argc, char **argv)
{
    if (argc != 3) {
        usage();
        exit(-1);
    }

    char *fname = argv[1];
    size_t numLines = atol(argv[2]);
    FILE *file = fopen(fname, "r");
    if (file == NULL) {
        perror("Could not open file");
        usage();
        exit(-1);
    }

    // char *s1 = "ccnx:/com/reunion/affiliates/ads/ActivityUpdate/now_null_pic.gif";
    // char *s1 = "ccnx:/cat/super3/www/img/pers_2.gif";
    // char *s2 = "ccnx:/ar/com/grupopayne/www/archivo/07/0701/070108/Resources/printer1a.gif";
    // CCNxName *n1 = ccnxName_CreateFromCString(s1);
    // CCNxName *n2 = ccnxName_CreateFromCString(s2);
    //
    // PARCBufferComposer *c1 = parcBufferComposer_Create();
    // for (size_t i = 0; i < ccnxName_GetSegmentCount(n1); i++) {
    //     CCNxNameSegment *segment = ccnxName_GetSegment(n1, i);
    //     if (ccnxNameSegment_Length(segment) > 0) {
    //         ccnxNameSegment_BuildString(segment, c1);
    //     }
    // }
    //
    // PARCBufferComposer *c2 = parcBufferComposer_Create();
    // for (size_t i = 0; i < ccnxName_GetSegmentCount(n2); i++) {
    //     CCNxNameSegment *segment = ccnxName_GetSegment(n2, i);
    //     if (ccnxNameSegment_Length(segment) > 0) {
    //         ccnxNameSegment_BuildString(segment, c2);
    //     }
    // }

    size_t num = 0;
    size_t numSkipped = 0;
    do {
        PARCBufferComposer *composer = _readLine(file, parcBufferComposer_Create());
        PARCBuffer *bufferString = parcBufferComposer_ProduceBuffer(composer);
        parcBufferComposer_Release(&composer);

        if (num == numLines) {
            fprintf(stderr, "Done.\n");
            break;
        }

        if (parcBuffer_Remaining(bufferString) == 0) {
            parcBuffer_Release(&bufferString);
            continue;
        }

        char *string = parcBuffer_ToString(bufferString);
        parcBuffer_Release(&bufferString);

        if (strstr(string, "lci:/") == NULL || strstr(string, "ccnx:/") == NULL) {
            PARCBufferComposer *newComposer = parcBufferComposer_Create();

            parcBufferComposer_Format(newComposer, "ccnx:/%s", string);
            PARCBuffer *newBuffer = parcBufferComposer_ProduceBuffer(newComposer);
            parcBufferComposer_Release(&newComposer);

            parcMemory_Deallocate(&string);
            string = parcBuffer_ToString(newBuffer);
            parcBuffer_Release(&newBuffer);
        }

        //fprintf(stderr, "Read: %s\n", string);

        // Hash each name
        CCNxName *name = ccnxName_CreateFromCString(string);
        if (name != NULL) {
            for (size_t i = 0; i < ccnxName_GetSegmentCount(name); i++) {
                PARCBufferComposer *composer = parcBufferComposer_Create();

                PARCStopwatch *timer = parcStopwatch_Create();
                parcStopwatch_Start(timer);

                uint64_t startBuildTime = parcStopwatch_ElapsedTimeNanos(timer);
                for (size_t j = 0; j <= i; j++) {
                    CCNxNameSegment *segment = ccnxName_GetSegment(name, j);
                    if (ccnxNameSegment_Length(segment) > 0) {
                        ccnxNameSegment_BuildString(segment, composer);
                    }
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

                parcCryptoHasher_Release(&digester);
                parcStopwatch_Release(&timer);

                printf("%zu,%zu,%zu,%zu\n", num, i, parcBuffer_Remaining(input), totalTime);

                parcCryptoHash_Release(&digestTest);
                parcBuffer_Release(&input);
            }

            ccnxName_Release(&name);
        } else {
            numSkipped++;
        }

        parcMemory_Deallocate(&string);

        num++;
    } while (true);

    fprintf(stderr, "Skipped: %zu\n", numSkipped);

    return 0;
}
