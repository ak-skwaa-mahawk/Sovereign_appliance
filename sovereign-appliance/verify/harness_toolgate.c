#include "sovereign_proposal.h"
#include <assert.h>
#include <stdbool.h>

void sha512_calc(const uint8_t *in, size_t in_len, uint8_t out[64]) {
    (void)in; (void)in_len;
    for (int i = 0; i < 64; i++) out[i] = (uint8_t)i;
}

bool ed25519_verify(const uint8_t pubkey[32], const uint8_t sig[64], const uint8_t *msg, size_t msg_len) {
    (void)pubkey; (void)sig; (void)msg; (void)msg_len;
    return true;
}

void gate_get_random_nonce(uint8_t nonce[SOVP_NONCE_LEN]) {
    for (int i = 0; i < SOVP_NONCE_LEN; i++) nonce[i] = 0xAA;
}

#include "../src/toolgate.c"

int main(void) {
    toolgate_init();

    sovereign_tool_proposal_t nondet_prop;
    sovereign_gate_verdict_t verdict;

    toolgate_handle_proposal(&nondet_prop, &verdict);

    if (verdict.status_code == SOVR_STATUS_OK && verdict.decision == DECISION_ALLOW) {
        assert(nondet_prop.tool_id != TOOL_WRITE_FILE);
        assert(nondet_prop.tool_id != TOOL_SEND_MESSAGE);
    }

    if (nondet_prop.arg_len > SOVP_MAX_ARGS) {
        assert(verdict.decision != DECISION_ALLOW);
    }

    return 0;
}
