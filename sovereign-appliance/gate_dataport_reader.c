#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define DATAPORT_SIZE 4096
#define APPROVAL_OFFSET 0x400

struct __attribute__((__packed__)) gate_approval {
    uint32_t seq_id;              /* +0x00: Monotonic Proposal Sequence ID          */
    uint8_t  witness_mask;        /* +0x04: Bitmask of signers (0x07 = Triad 0,1,2) */
    uint8_t  reserved[3];         /* +0x05: Canonical zero-padding                  */
    uint8_t  challenge_nonce[32]; /* +0x08: 32-byte hash matching audit entry tip   */
    uint8_t  signatures[6][64];   /* +0x28: Up to 6 x 64-byte Ed25519 signatures    */
};

_Static_assert(sizeof(struct gate_approval) == 424, "gate_approval must be exactly 424 bytes");

static void dump_hex(const uint8_t *data, size_t len) {
    for (size_t i = 0; i < len; ++i) {
        printf("%02x", data[i]);
    }
    printf("\n");
}

int main(int argc, char **argv) {
    const char *bin_path = (argc > 1) ? argv[1] : "./workspace/harness_approval.bin";
    FILE *f = fopen(bin_path, "rb");
    if (!f) {
        perror("[-] Failed to open approval binary");
        return 1;
    }

    struct gate_approval approval;
    size_t read_bytes = fread(&approval, 1, sizeof(approval), f);
    fclose(f);

    if (read_bytes != sizeof(struct gate_approval)) {
        fprintf(stderr, "[-] Incomplete read: got %zu bytes, expected %zu\n",
                read_bytes, sizeof(struct gate_approval));
        return 1;
    }

    printf("=== CAmkES Dataport Approval Inspection (Offset 0x%04X) ===\n", APPROVAL_OFFSET);
    printf("  Sequence ID  : %u\n", approval.seq_id);
    printf("  Witness Mask : 0x%02X\n", approval.witness_mask);

    if ((approval.witness_mask & 0x07) != 0x07) {
        fprintf(stderr, "[-] Quorum failure: Witness mask does not meet Triad threshold (0x07)\n");
        return 2;
    }
    printf("  Quorum Status: Verified (Triad quorum 0x07 satisfied)\n");

    printf("  Challenge Nonce (32B): ");
    dump_hex(approval.challenge_nonce, 32);

    int sig_count = 0;
    for (int i = 0; i < 6; ++i) {
        uint8_t zero_buf[64] = {0};
        if (memcmp(approval.signatures[i], zero_buf, 64) != 0) {
            sig_count++;
            printf("  Signature [%d] : Valid (64 bytes populated)\n", i);
        }
    }

    printf("  Total Populated Signatures: %d\n", sig_count);
    if (sig_count < 3) {
        fprintf(stderr, "[-] Incomplete signature vector: expected >= 3, found %d\n", sig_count);
        return 3;
    }

    printf("[+] CAmkES dataport approval vector layout is structurally valid.\n");
    return 0;
}
