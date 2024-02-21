DAC_MAX_SAMPLE_RATE = 6.8e3  # MHz
ADC_MAX_SAMPLE_RATE = 2.5e3  # MHz


def find_opt_pll_param(ref_clk_freq, fb_div_range, output_div_range, vco_range, samp_limit):
    min_delta = float('inf')
    best_pair = (None, None)

    for fb in fb_div_range:
        for M in output_div_range:
            vco_freq = ref_clk_freq * fb
            err = samp_limit - vco_freq / M
            if 0 < err < min_delta and vco_range[0] < vco_freq < vco_range[1]:
                min_delta = err
                best_pair = (fb, M)

    return best_pair, min_delta


# DAC parameter
ref_clk_freq = 409.6
fb_div_range = range(13, 161)  # fb from 13 to 160 inclusive
vco_range = [7863, 13760]
# M is 1 or even numbers up to 64
output_div_range = [1] + [i for i in range(2, 65) if i % 2 == 0]

# Find the optimal pair
optimal_pair, optimal_delta = find_opt_pll_param(
    ref_clk_freq, fb_div_range, output_div_range, vco_range, DAC_MAX_SAMPLE_RATE)
print(
    f"DAC optimal_pair: fb={optimal_pair[0]}, M={optimal_pair[1]}, optimal_delta:{optimal_delta} MHz, sample_rate: {DAC_MAX_SAMPLE_RATE-optimal_delta}MHz")

# ADC parameter
vco_range = [8500, 13200]
# M is 1 or even numbers up to 64
output_div_range = [i for i in range(2, 65) if i % 2 == 0]

# Find the optimal pair
optimal_pair, optimal_delta = find_opt_pll_param(
    ref_clk_freq, fb_div_range, output_div_range, vco_range, ADC_MAX_SAMPLE_RATE)
print(
    f"ADC optimal_pair: fb={optimal_pair[0]}, M={optimal_pair[1]}, optimal_delta:{optimal_delta} MHz, sample_rate: {ADC_MAX_SAMPLE_RATE-optimal_delta}MHz")
