#pragma once

#include <cstdint>
#include <cmath>
#include <algorithm>

class DualRailPowerBalancer {
public:
    enum class State {
        DISABLED,
        AUTO_TUNING_RELAY,
        ACTIVE_PID_CONTROL,
        FAULT_OVERVOLTAGE
    };

    struct TuningParameters {
        float Kp = 0.0f;
        float Ki = 0.0f;
        float Kd = 0.0f;
        float ultimate_gain_Ku = 0.0f;
        float ultimate_period_Tu = 0.0f;
    };

    DualRailPowerBalancer(float target_v_diff = 0.0f, float max_rail_limit = 3.3f)
        : target_diff_(target_v_diff),
          max_rail_limit_(max_rail_limit),
          state_(State::DISABLED) {}

    void initialize(float sample_rate_hz) {
        dt_ = 1.0f / sample_rate_hz;
        reset();
    }

    void start_autotune(float relay_amplitude = 0.4f, float hysteresis = 0.02f) {
        relay_d_ = relay_amplitude;
        relay_hysteresis_ = hysteresis;
        tune_cycle_count_ = 0;
        peak_high_ = -999.0f;
        peak_low_ = 999.0f;
        last_zero_cross_time_ = 0.0f;
        accumulated_time_ = 0.0f;
        state_ = State::AUTO_TUNING_RELAY;
    }

    float step(float v_plus, float v_minus) {
        float diff_error = (v_plus - std::abs(v_minus)) - target_diff_;

        if (v_plus > max_rail_limit_ || std::abs(v_minus) > max_rail_limit_) {
            state_ = State::FAULT_OVERVOLTAGE;
            return 0.0f;
        }

        switch (state_) {
            case State::AUTO_TUNING_RELAY:
                return process_relay_autotune(diff_error);
            case State::ACTIVE_PID_CONTROL:
                return process_pid_control(diff_error);
            case State::FAULT_OVERVOLTAGE:
            case State::DISABLED:
            default:
                return 0.0f;
        }
    }

    State get_state() const { return state_; }
    TuningParameters get_tuning_params() const { return params_; }

private:
    float target_diff_;
    float max_rail_limit_;
    float dt_ = 0.0001f;
    State state_;

    TuningParameters params_;
    float integral_accum_ = 0.0f;
    float prev_error_ = 0.0f;
    float lpf_derivative_ = 0.0f;
    const float alpha_d_ = 0.15f;

    float relay_d_ = 0.4f;
    float relay_hysteresis_ = 0.02f;
    float relay_output_ = 0.0f;
    float peak_high_ = -999.0f;
    float peak_low_ = 999.0f;
    float last_zero_cross_time_ = 0.0f;
    float accumulated_time_ = 0.0f;
    uint32_t tune_cycle_count_ = 0;
    static constexpr uint32_t REQUIRED_CYCLES = 5;

    void reset() {
        integral_accum_ = 0.0f;
        prev_error_ = 0.0f;
        lpf_derivative_ = 0.0f;
    }

    float process_relay_autotune(float error) {
        accumulated_time_ += dt_;

        if (error > peak_high_) peak_high_ = error;
        if (error < peak_low_)  peak_low_  = error;

        if (error > relay_hysteresis_) {
            relay_output_ = -relay_d_;
        } else if (error < -relay_hysteresis_) {
            relay_output_ = relay_d_;
        }

        if ((prev_error_ < 0.0f && error >= 0.0f) || (prev_error_ > 0.0f && error <= 0.0f)) {
            if (tune_cycle_count_ > 0) {
                float half_period = accumulated_time_ - last_zero_cross_time_;
                params_.ultimate_period_Tu = half_period * 2.0f;
            }
            last_zero_cross_time_ = accumulated_time_;
            tune_cycle_count_++;

            if (tune_cycle_count_ >= (REQUIRED_CYCLES * 2)) {
                synthesize_pid_gains();
                reset();
                state_ = State::ACTIVE_PID_CONTROL;
            }
        }

        prev_error_ = error;
        return relay_output_;
    }

    void synthesize_pid_gains() {
        float peak_to_peak_amplitude = (peak_high_ - peak_low_) / 2.0f;
        if (peak_to_peak_amplitude <= 0.0001f) peak_to_peak_amplitude = 0.0001f;

        params_.ultimate_gain_Ku = (4.0f * relay_d_) / (3.14159265f * peak_to_peak_amplitude);
        params_.Kp = 0.45f * params_.ultimate_gain_Ku;
        params_.Ki = params_.Kp / (2.2f * params_.ultimate_period_Tu);
        params_.Kd = params_.Kp * (params_.ultimate_period_Tu / 6.3f);
    }

    float process_pid_control(float error) {
        float P = params_.Kp * error;
        integral_accum_ += error * dt_;
        float I = std::clamp(params_.Ki * integral_accum_, -1.0f, 1.0f);

        float raw_derivative = (error - prev_error_) / dt_;
        lpf_derivative_ = (alpha_d_ * raw_derivative) + ((1.0f - alpha_d_) * lpf_derivative_);
        float D = params_.Kd * lpf_derivative_;

        prev_error_ = error;
        return std::clamp(P + I + D, -1.5f, 1.5f);
    }
};
