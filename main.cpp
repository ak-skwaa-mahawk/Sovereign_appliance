#include <iostream>
#include <iomanip>
#include <thread>
#include <chrono>
#include "dual_rail_pid_autotuner.hpp"

int main() {
    DualRailPowerBalancer balancer(0.0f, 3.8f);
    balancer.initialize(10000.0f); // 10 kHz Rate

    std::cout << "====================================================\n";
    std::cout << "⚡ PROCESSOR 1: 3-0-3 DUAL-RAIL AUTO-TUNER RUNTIME\n";
    std::cout << "====================================================\n";

    balancer.start_autotune(0.4f, 0.002f);

    float v_pos = 3.20f;
    float v_neg = -2.80f;
    float control_adj = 0.0f;
    float integral_plant_state = 0.40f;
    uint64_t step = 0;
    bool logged_tuning = false;

    // Infinite real-time control loop
    while (true) {
        integral_plant_state += (-0.005f * integral_plant_state + 0.08f * control_adj);
        v_pos = 3.0f + (integral_plant_state * 0.5f);
        v_neg = -(3.0f - (integral_plant_state * 0.5f));

        float noise = ((step % 5) - 2) * 0.0005f;
        control_adj = balancer.step(v_pos + noise, v_neg);

        if (balancer.get_state() == DualRailPowerBalancer::State::ACTIVE_PID_CONTROL && !logged_tuning) {
            auto p = balancer.get_tuning_params();
            std::cout << "✔ Auto-Tuning Complete & PID Active:\n";
            std::cout << "   -> Ultimate Gain (Ku)   : " << p.ultimate_gain_Ku << "\n";
            std::cout << "   -> Ultimate Period (Tu) : " << p.ultimate_period_Tu << " s\n";
            std::cout << "   -> Proportional (Kp)    : " << p.Kp << "\n";
            std::cout << "   -> Integral (Ki)        : " << p.Ki << "\n";
            std::cout << "   -> Derivative (Kd)      : " << p.Kd << "\n";
            std::cout << "⚡ Entering continuous 10kHz balancing loop...\n";
            logged_tuning = true;
        }

        step++;
        std::this_thread::sleep_for(std::chrono::microseconds(100)); // 100us = 10kHz
    }

    return 0;
}
