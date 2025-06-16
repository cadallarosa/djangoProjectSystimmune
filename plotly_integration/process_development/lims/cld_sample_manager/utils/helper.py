def calculate_recoveries(sample):
    fast_pro_a_recovery = None
    a280_recovery = None

    try:
        if all([
            sample.proa_eluate_volume is not None,
            sample.pro_aqa_e_titer is not None,
            sample.hccf_loading_volume is not None,
            sample.pro_aqa_hf_titer is not None
        ]):
            fast_pro_a_recovery = (
                                          sample.proa_eluate_volume * sample.pro_aqa_e_titer
                                  ) / (
                                          sample.hccf_loading_volume * sample.pro_aqa_hf_titer
                                  ) * 100

        if all([
            sample.proa_eluate_volume is not None,
            sample.proa_eluate_a280_conc is not None,
            sample.hccf_loading_volume is not None,
            sample.pro_aqa_hf_titer is not None
        ]):
            a280_recovery = (
                                    sample.proa_eluate_volume * sample.proa_eluate_a280_conc
                            ) / (
                                    sample.hccf_loading_volume * sample.pro_aqa_hf_titer
                            ) * 100
    except ZeroDivisionError:
        pass

    return (
        round(fast_pro_a_recovery, 1) if fast_pro_a_recovery is not None else None,
        round(a280_recovery, 1) if a280_recovery is not None else None,
    )