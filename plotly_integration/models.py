from django.db import models

#Empower HPLC Tables
class SampleMetadata(models.Model):
    id = models.AutoField(primary_key=True)
    result_id = models.IntegerField()
    system_name = models.CharField(max_length=255)
    project_name = models.CharField(max_length=255, null=True, blank=True)
    sample_prefix = models.CharField(max_length=255, null=True, blank=True)
    sample_number = models.IntegerField(null=True, blank=True)
    sample_suffix = models.CharField(max_length=255, null=True, blank=True)
    sample_type = models.CharField(max_length=255, null=True, blank=True)
    analysis_type = models.IntegerField(null=True, blank=True) #1:SEC,2:PROA
    sample_name = models.CharField(max_length=255, null=True, blank=True)  # ✅ Fixed
    sample_set_id = models.IntegerField(null=True, blank=True)
    sample_set_name = models.CharField(max_length=255, null=True, blank=True)
    date_acquired = models.DateTimeField(null=True, blank=True)  # ✅ Changed from DateTimeField
    acquired_by = models.CharField(max_length=255, null=True, blank=True)
    run_time = models.FloatField(null=True, blank=True)
    processing_method = models.CharField(max_length=255, null=True, blank=True)
    processed_channel_description = models.CharField(max_length=255, null=True, blank=True)
    injection_volume = models.FloatField(null=True, blank=True)
    injection_id = models.IntegerField(null=True, blank=True)
    column_name = models.CharField(max_length=255, null=True, blank=True)
    column_serial_number = models.CharField(max_length=255, null=True, blank=True)
    column_id = models.ForeignKey('EmpowerColumnLogbook',on_delete=models.SET_NULL,null=True,db_column="column_id",to_field="id")
    instrument_method_id = models.IntegerField(null=True, blank=True)
    instrument_method_name = models.CharField(max_length=255, null=True, blank=True)
    dilution = models.FloatField(null=True, blank=True)


    class Meta:
        db_table = 'sample_metadata'
        managed = True
        unique_together = ('result_id', 'system_name')


class PeakResults(models.Model):
    id = models.AutoField(primary_key=True)
    result_id = models.IntegerField()
    system_name = models.CharField(max_length=255, null=True, blank=True)
    channel_name = models.CharField(max_length=255, null=True, blank=True)  # ✅ Fixed
    peak_name = models.CharField(max_length=255, null=True, blank=True)
    peak_retention_time = models.FloatField(null=True, blank=True)
    peak_start_time = models.FloatField(null=True, blank=True)
    peak_end_time = models.FloatField(null=True, blank=True)
    area = models.IntegerField(null=True, blank=True)
    percent_area = models.FloatField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    asym_at_10 = models.FloatField(null=True, blank=True)
    plate_count = models.FloatField(null=True, blank=True)
    res_hh = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'peak_results'
        managed = True
        unique_together = ('result_id', 'peak_retention_time')


class ChromMetadata(models.Model):
    id = models.AutoField(primary_key=True)
    result_id = models.IntegerField()
    system_name = models.CharField(max_length=255)
    sample_name = models.CharField(max_length=255, null=True, blank=True)  # ✅ Fixed
    sample_set_name = models.CharField(max_length=255, null=True, blank=True)
    sample_set_id = models.IntegerField(null=True, blank=True)
    channel_1 = models.CharField(max_length=255, null=True, blank=True)
    channel_2 = models.CharField(max_length=255, null=True, blank=True)
    channel_3 = models.CharField(max_length=255, null=True, blank=True)
    average_pressure = models.FloatField(null=True, blank=True)
    max_pressure = models.FloatField(null=True, blank=True)  # New field
    min_pressure = models.FloatField(null=True, blank=True)  # New field
    pressure_variance = models.FloatField(null=True, blank=True)  # New field
    pressure_stddev = models.FloatField(null=True, blank=True)  # New field
    retention_time_range = models.FloatField(null=True, blank=True)  # New field
    peak_pressure_time = models.FloatField(null=True, blank=True)  # New field

    class Meta:
        db_table = 'chrom_metadata'
        managed = True
        unique_together = ('result_id', 'system_name')


class TimeSeriesData(models.Model):
    id = models.AutoField(primary_key=True)
    result_id = models.IntegerField()
    system_name = models.CharField(max_length=255)
    time = models.FloatField()
    channel_1 = models.FloatField(null=True, blank=True)
    channel_2 = models.FloatField(null=True, blank=True)
    channel_3 = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'time_series_data'
        managed = True
        unique_together = ('result_id', 'time')

class EmpowerColumnLogbook(models.Model):
    id = models.AutoField(primary_key=True)  # Integer primary key
    column_serial_number = models.CharField(max_length=255, unique=True)  # Unique serial number
    column_name = models.CharField(max_length=255)
    total_injections = models.IntegerField(default=0)
    most_recent_injection_date = models.DateField(null=True, blank=True)  # ✅ Fixed

    class Meta:
        db_table = 'empower_column_logbook'
        managed = True

class SystemInformation(models.Model):
    system_name = models.CharField(max_length=255, primary_key=True)  # ✅ Fixed
    channel_1 = models.CharField(max_length=255, null=True, blank=True)
    channel_2 = models.CharField(max_length=255, null=True, blank=True)
    channel_3 = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'system_information'
        managed = True

#django Specific Tables
class ProjectID(models.Model):
    project = models.CharField(max_length=255, null=True, blank=True)
    sip_number = models.CharField(max_length=255, null=True, blank=True)
    fb_id = models.CharField(max_length=255, primary_key=True)  # ✅ Primary Key
    cell_line = models.CharField(max_length=255, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    analyst = models.CharField(max_length=255, null=True, blank=True)
    harvest_date = models.DateField(null=True, blank=True)
    unifi_number = models.CharField(max_length=255, null=True, blank=True)
    titer_comment = models.TextField(null=True, blank=True)
    cld_30ml_octet_titer = models.FloatField(null=True, blank=True)
    pro_aqa_titer = models.FloatField(null=True, blank=True)
    fast_pro_a_recovery = models.FloatField(null=True, blank=True)
    purification_recovery_a280 = models.FloatField(null=True, blank=True)
    proa_eluate_a280_conc = models.FloatField(null=True, blank=True)
    proa_eluate_volume = models.FloatField(null=True, blank=True)
    hccf_loading_volume = models.FloatField(null=True, blank=True)
    proa_recovery = models.FloatField(null=True, blank=True)
    proa_column_size = models.FloatField(null=True, blank=True)
    column_id = models.CharField(max_length=255, null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    sec_2_wks_a_conc = models.FloatField(null=True, blank=True)  # ✅ New Field
    sec_2wks_n_conc = models.FloatField(null=True, blank=True)  # ✅ New Field

    class Meta:
        db_table = 'project_id'
        managed = True



class Report(models.Model):
    report_id = models.AutoField(primary_key=True)
    report_name = models.CharField(max_length=255, null=True, blank=True)
    project_id = models.CharField(max_length=255, null=True, blank=True)
    analysis_type = models.IntegerField(null=True, blank=True)
    sample_type = models.CharField(max_length=255, null=True, blank=True)
    selected_samples = models.TextField(null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    date_created = models.DateTimeField(null=True, blank=True)
    selected_result_ids = models.TextField(null=True, blank=True)
    department = models.IntegerField(null=True, blank=True) #1 = Process Development, 2 = Protein Engineering

    class Meta:
        db_table = 'report'
        managed = True


class Users(models.Model):
    user_id = models.IntegerField()
    user_name = models.CharField(max_length=255, primary_key=True)  # ✅ Fixed
    user_initials = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        db_table = 'users'
        managed = True


class Method(models.Model):
    method_id = models.AutoField(primary_key=True)
    method_type = models.IntegerField(null=True, blank=True)
    new_column_1 = models.IntegerField(null=True, blank=True)
    new_column_2 = models.IntegerField(null=True, blank=True)
    new_column_3 = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'method'
        managed = True


class ReportInstance(models.Model):
    report_instance_id = models.AutoField(primary_key=True)
    exclusions = models.TextField(null=True, blank=True)
    report_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'report_instance'
        managed = True


class Results(models.Model):
    id = models.AutoField(primary_key=True)
    result_id = models.IntegerField()
    system_name = models.CharField(max_length=255, null=True, blank=True)  # ✅ Fixed
    project_name = models.CharField(max_length=255, null=True, blank=True)  # ✅ Fixed
    sample_set_id = models.IntegerField(null=True, blank=True)
    sample_set_name = models.CharField(max_length=255, null=True, blank=True)
    acquired_by = models.CharField(max_length=255, null=True, blank=True)
    column_serial_number = models.CharField(max_length=255, null=True, blank=True)
    new_column = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'results'
        managed = True


class ProjectInformation(models.Model):
    protein = models.TextField(null=True, blank=True)
    project = models.TextField()
    project_description = models.TextField(null=True, blank=True)
    molecule_type = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    purifications = models.TextField(null=True, blank=True)
    plasmids = models.TextField(null=True, blank=True)
    plasmid_description = models.TextField(null=True, blank=True)
    tags = models.TextField(null=True, blank=True)
    transfections = models.TextField(null=True, blank=True)
    titer = models.FloatField(null=True, blank=True)  # Titer [μg/mL]
    protein_concentration = models.FloatField(null=True, blank=True)  # Protein Concentration [mg/mL]
    nanodrop_e1 = models.FloatField(null=True, blank=True)
    molecular_weight = models.FloatField(null=True, blank=True)  # Molecular Weight [Da]
    percent_poi = models.FloatField(null=True, blank=True)  # % POI
    pi = models.FloatField(null=True, blank=True)  # pI
    latest_purification_date = models.DateTimeField(null=True, blank=True)
    purified = models.BooleanField(default=False)  # Boolean field for 'Purified'

    class Meta:
        db_table = 'project_information'
        managed = True


###UFDF/Viral Filtration Models

class UFDFMetadata(models.Model):
    result_id = models.AutoField(primary_key=True)  # Auto-incremented result ID
    molecule_name = models.TextField()
    experiment_name = models.TextField()
    experimental_notes = models.TextField(blank=True, null=True)

    cassette_type = models.TextField(null=True, blank=True)
    load_concentration = models.FloatField(null=True, blank=True)
    load_volume = models.FloatField(null=True, blank=True)
    load_mass = models.FloatField(null=True, blank=True)

    system_void_volume = models.FloatField(null=True, blank=True)
    target_diafiltration_concentration = models.FloatField(null=True, blank=True)

    uf1_target_reservoir_mass = models.FloatField(null=True, blank=True)
    diavolumes = models.IntegerField(null=True, blank=True)
    permeate_target_mass = models.FloatField(null=True, blank=True)
    diafiltration_volume_required = models.FloatField(null=True, blank=True)

    lmh_target = models.FloatField(null=True, blank=True)
    flow_rate = models.FloatField(null=True, blank=True)
    target_flow_rate = models.FloatField(null=True, blank=True)
    target_p2500_setpoint = models.FloatField(null=True, blank=True)
    target_p3000_setpoint = models.FloatField(null=True, blank=True)

    recovery = models.FloatField(null=True, blank=True)
    final_volume = models.FloatField(null=True, blank=True)
    final_concentration = models.FloatField(null=True, blank=True)
    product_mass = models.FloatField(null=True, blank=True)
    yield_percentage = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for record creation

    class Meta:
        db_table = "ufdf_metadata"



class SartoflowTimeSeriesData(models.Model):
    id = models.AutoField(primary_key=True)
    result_id = models.ForeignKey(UFDFMetadata, on_delete=models.CASCADE,null=True, blank=True)
    batch_id = models.CharField(max_length=255)
    pdat_time = models.DateTimeField()
    process_time = models.FloatField(null=True, blank=True)

    ag2100_value = models.FloatField(null=True, blank=True)
    ag2100_setpoint = models.FloatField(null=True, blank=True)
    ag2100_mode = models.IntegerField(null=True, blank=True)
    ag2100_output = models.FloatField(null=True, blank=True)

    dpress_value = models.FloatField(null=True, blank=True)
    dpress_output = models.FloatField(null=True, blank=True)
    dpress_mode = models.IntegerField(null=True, blank=True)
    dpress_setpoint = models.FloatField(null=True, blank=True)

    f_perm_value = models.FloatField(null=True, blank=True)

    p2500_setpoint = models.FloatField(null=True, blank=True)
    p2500_value = models.FloatField(null=True, blank=True)
    p2500_output = models.FloatField(null=True, blank=True)
    p2500_mode = models.IntegerField(null=True, blank=True)

    p3000_setpoint = models.FloatField(null=True, blank=True)
    p3000_mode = models.IntegerField(null=True, blank=True)
    p3000_output = models.FloatField(null=True, blank=True)
    p3000_value = models.FloatField(null=True, blank=True)
    p3000_t = models.FloatField(null=True, blank=True)

    pir2600 = models.FloatField(null=True, blank=True)
    pir2700 = models.FloatField(null=True, blank=True)

    pirc2500_value = models.FloatField(null=True, blank=True)
    pirc2500_output = models.FloatField(null=True, blank=True)
    pirc2500_setpoint = models.FloatField(null=True, blank=True)
    pirc2500_mode = models.IntegerField(null=True, blank=True)

    qir2000 = models.FloatField(null=True, blank=True)
    qir2100 = models.FloatField(null=True, blank=True)

    tir2100 = models.FloatField(null=True, blank=True)
    tmp = models.FloatField(null=True, blank=True)

    wir2700 = models.FloatField(null=True, blank=True)

    wirc2100_output = models.FloatField(null=True, blank=True)
    wirc2100_setpoint = models.FloatField(null=True, blank=True)
    wirc2100_mode = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.batch_id} - {self.pdat_time}"

    class Meta:
        db_table = "sartoflow_time_series_data"
        managed = True

class VFMetadata(models.Model):
    result_id = models.AutoField(primary_key=True)  # Auto-incremented result ID
    molecule_name = models.TextField()
    experiment_name = models.TextField()
    experimental_notes = models.TextField(blank=True, null=True)
    filter_type = models.TextField(null=True, blank=True)
    load_concentration = models.FloatField(null=True, blank=True)
    load_volume = models.FloatField(null=True, blank=True)
    load_mass = models.FloatField(null=True, blank=True)
    target_pressure = models.FloatField(null=True, blank=True)
    final_volume = models.FloatField(null=True, blank=True)
    final_concentration = models.FloatField(null=True, blank=True)
    product_mass = models.FloatField(null=True, blank=True)
    yield_percentage = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for record creation

    class Meta:
        db_table = "vf_metadata"

class VFTimeSeriesData(models.Model):
    id = models.AutoField(primary_key=True)
    result_id = models.ForeignKey(VFMetadata, on_delete=models.CASCADE,null=True, blank=True)
    unit_step = models.BigIntegerField(null=True, blank=True) # 1= Water Flush, 2= Buffer Flush, 3=Product Filtration
    batch_id = models.CharField(max_length=255)
    pdat_time = models.DateTimeField()
    process_time = models.FloatField(null=True, blank=True)
    pir2700 = models.FloatField(null=True, blank=True)
    wir2700 = models.FloatField(null=True, blank=True)
    f_perm_value = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.batch_id} - {self.pdat_time}"

    class Meta:
        db_table = "vf_time_series_data"
        managed = True

# '''Akta Models for table'''


class AktaResult(models.Model):
    id = models.AutoField(primary_key=True)  # Ensure primary key is explicitly set
    result_id = models.CharField(max_length=50, unique=True)
    column_name = models.TextField(null=True, blank=True)
    column_volume = models.TextField(null=True, blank=True)
    method = models.TextField(null=True, blank=True)
    result_path = models.TextField(null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)
    user = models.CharField(max_length=255, null=True, blank=True)
    sample_id = models.CharField(max_length=255, null=True, blank=True)
    run_type = models.BigIntegerField(null=True, blank=True)
    scouting_id = models.BigIntegerField(null=True, blank=True)
    scouting_run_num = models.BigIntegerField(null=True, blank=True)
    group_id = models.BigIntegerField(null=True, blank=True)
    system = models.CharField(max_length=255, null=True, blank=True)
    source_material_id = models.BigIntegerField(null=True, blank=True)
    downstream_step_id = models.BigIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'akta_result'

    # def __str__(self):
    #     return f"Result ID: {self.result_id} | User: {self.user} | Date: {self.date}"


class AktaColumnsCharacteristics(models.Model):
    column_id = models.BigAutoField(primary_key=True)
    column_type = models.CharField(max_length=255)
    technique = models.CharField(max_length=255)
    column_volume = models.FloatField()
    diameter = models.FloatField()
    bed_height = models.FloatField()
    resin = models.CharField(max_length=255)
    alias = models.CharField(max_length=255)
    asymmetry = models.FloatField()
    plates_per_meter = models.FloatField()
    HETP = models.FloatField()
    num_cycles = models.BigIntegerField()
    avg_starting_pressure = models.FloatField()

    class Meta:
        db_table = 'akta_columns_characteristics'


class AktaMethodInformation(models.Model):
    id = models.BigAutoField(primary_key=True)
    method_name = models.CharField(max_length=255)
    last_saved = models.DateTimeField()
    created_by_user = models.CharField(max_length=255)
    method_notes = models.TextField()
    result_name = models.CharField(max_length=255)
    start_notes = models.TextField()
    scouting = models.BigIntegerField()
    created_for_system = models.CharField(max_length=255)

    class Meta:
        db_table = 'akta_method_information'


class AktaChromatogram(models.Model):
    ml = models.FloatField()  # Volume in mL
    result_id = models.CharField(max_length=50, null=True, blank=True)
    uv_1_280 = models.FloatField(null=True, blank=True)  # UV Absorbance at 280nm
    uv_2_0 = models.FloatField(null=True, blank=True)
    uv_3_0 = models.FloatField(null=True, blank=True)
    cond = models.FloatField(null=True, blank=True)  # Conductivity
    conc_b = models.FloatField(null=True, blank=True)  # Concentration B
    pH = models.FloatField(null=True, blank=True)
    system_flow = models.FloatField(null=True, blank=True)
    system_linear_flow = models.FloatField(null=True, blank=True)
    system_pressure = models.FloatField(null=True, blank=True)
    cond_temp = models.FloatField(null=True, blank=True)
    sample_flow = models.FloatField(null=True, blank=True)
    sample_linear_flow = models.FloatField(null=True, blank=True)
    sample_pressure = models.FloatField(null=True, blank=True)
    preC_pressure = models.FloatField(null=True, blank=True)
    deltaC_pressure = models.FloatField(null=True, blank=True)
    postC_pressure = models.FloatField(null=True, blank=True)
    frac_temp = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "akta_chromatogram"

    # def __str__(self):
    #     return f"Result: {self.result.result_id} | ml: {self.ml}"


class AktaFraction(models.Model):
    result_id = models.CharField(max_length=50, null=True, blank=True)
    ml = models.FloatField(null=True, blank=True)
    fraction = models.CharField(max_length=100, null=True, blank=True)  # Example column

    class Meta:
        db_table = "akta_fraction"
    # def __str__(self):
    #     return f"Result: {self.result.result_id} | Fraction at ml: {self.ml}"


class AktaRunLog(models.Model):
    result_id = models.CharField(max_length=50, null=True, blank=True)
    ml = models.FloatField(null=True, blank=True)
    log_text = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "akta_run_log"

    # def __str__(self):
    #     return f"Result: {self.result.result_id} | Log at ml: {self.ml}"


class AktaScoutingList(models.Model):
    scouting_id = models.BigAutoField(primary_key=True)
    total_num_of_scoutings = models.BigIntegerField()
    run_scouting = models.BigIntegerField()
    run = models.BigIntegerField()
    scouting = models.BooleanField()
    variable = models.TextField()
    block = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=255)
    value = models.FloatField()

    class Meta:
        db_table = 'akta_scouting_list'


class PDSamples(models.Model):
    id = models.AutoField(primary_key=True)  # Ensure primary key is explicitly set
    result_id = models.IntegerField()
    pd_number = models.CharField(max_length=255)  # PD#
    sample_volume_ul = models.FloatField()  # Sample volume (uL)
    identifier = models.CharField(max_length=255)  # Identifier (SM/DN)
    description_volume = models.TextField()  # Description + Volume
    a280_date = models.DateField(null=True, blank=True)  # A280 date
    concentration_mg_ml = models.FloatField(null=True, blank=True)  # mg/ml
    sec_date = models.DateField(null=True, blank=True)  # SEC date
    hmw_percentage = models.FloatField(null=True, blank=True)
    mp_percentage = models.FloatField(null=True, blank=True)  # MP%
    lmw_percentage = models.FloatField(null=True, blank=True)
    sec_total_area = models.FloatField(null=True, blank=True)
    sec_injection_ug = models.FloatField(null=True, blank=True)  # Injection (ug)
    sec_dilution = models.FloatField(null=True, blank=True)  # Dilution
    sec_load_volume_ul = models.FloatField(null=True, blank=True)  # SEC load volume (uL)
    hplc_proa_titer_mg_ml = models.FloatField(null=True, blank=True)  # HPLC-ProA Titer (mg/mL)
    hcp_ppm = models.FloatField(null=True, blank=True)  # HCP (ppm)
    proa_ppm = models.FloatField(null=True, blank=True)  # ProA (ppm)
    dna_ppm = models.FloatField(null=True, blank=True)  # DNA (ppm)
    akta_fraction_id = models.CharField(max_length=255, null=True, blank=True)  # AKTA Fraction ID

    class Meta:
        db_table = 'pd_samples'


class DnAssignment(models.Model):
    dn = models.CharField(max_length=255)
    project_id = models.CharField(max_length=255)
    study_name = models.CharField(max_length=255)
    description_of_purpose = models.TextField()
    load_volume = models.FloatField()
    notes = models.TextField()

    class Meta:
        db_table = 'dn_assignment'



#Cell Culture Models

#Nova Flex 2 Models
class NovaFlex2(models.Model):
    id = models.AutoField(primary_key=True)  # Ensure primary key is explicitly set
    date_time = models.DateTimeField()
    sample_id = models.CharField(max_length=255)
    sample_type = models.IntegerField(null=True, blank=True) # 1 = UP, 2 = CLD , 3 = Uncategorized
    gln = models.FloatField(null=True, blank=True)
    glu = models.FloatField(null=True, blank=True)
    gluc = models.FloatField(null=True, blank=True)
    lac = models.FloatField(null=True, blank=True)
    nh4 = models.FloatField(null=True, blank=True)
    pH = models.FloatField(null=True, blank=True)
    po2 = models.FloatField(null=True, blank=True)
    pco2 = models.FloatField(null=True, blank=True)
    osm = models.FloatField(null=True, blank=True)

    # New fields to store parsed sample information
    experiment = models.CharField(max_length=50, null=True, blank=True)
    day = models.IntegerField(null=True, blank=True)
    reactor_type = models.CharField(max_length=10, null=True, blank=True)
    reactor_number = models.IntegerField(null=True, blank=True)
    special = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'nova_flex_2'
        unique_together = ('date_time', 'sample_id')  # Enforce uniqueness

class NovaReport(models.Model):
    id = models.AutoField(primary_key=True)  # Ensure primary key is explicitly set
    report_name = models.CharField(max_length=255)
    project_id = models.CharField(max_length=255, null=True, blank=True)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    department = models.IntegerField(null=True, blank=True) # 1 = UP, 2 = CLD , 3 = Uncategorized
    comments = models.TextField(null=True, blank=True)
    selected_result_ids = models.TextField()  # Stores comma-separated result IDs
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'nova_report'


#Vicell Models
class ViCellData(models.Model):
    id = models.AutoField(primary_key=True)  # Ensure primary key is explicitly set
    sample_id = models.CharField(max_length=100, unique=True)
    date_time = models.DateTimeField(null=True, blank=True)
    experiment = models.CharField(max_length=50, null=True, blank=True)
    day = models.IntegerField(null=True, blank=True)
    reactor_type = models.CharField(max_length=10, null=True, blank=True)
    reactor_number = models.IntegerField(null=True, blank=True)
    special = models.CharField(max_length=50, null=True, blank=True)
    cell_count = models.FloatField(null=True, blank=True)
    viable_cells = models.FloatField(null=True, blank=True)
    total_cells_per_ml = models.FloatField(null=True, blank=True)
    viable_cells_per_ml = models.FloatField(null=True, blank=True)
    viability = models.FloatField(null=True, blank=True)
    average_diameter = models.FloatField(null=True, blank=True)
    average_viable_diameter = models.FloatField(null=True, blank=True)
    average_circularity = models.FloatField(null=True, blank=True)
    average_viable_circularity = models.FloatField(null=True, blank=True)
    sample_type = models.IntegerField(null=True, blank=True)  # 1 = UP, 2 = CLD , 3 = Uncategorized


    class Meta:
        db_table = 'vicell_data'
        unique_together = ('date_time', 'sample_id')  # Enforce uniqueness

class ViCellReport(models.Model):
    id = models.AutoField(primary_key=True)  # Ensure primary key is explicitly set
    report_name = models.CharField(max_length=255)
    project_id = models.CharField(max_length=255, null=True, blank=True)
    user_id = models.CharField(max_length=255, null=True, blank=True)
    department = models.IntegerField(null=True, blank=True)  # 1 = UP, 2 = CLD , 3 = Uncategorized
    comments = models.TextField(null=True, blank=True)
    selected_result_ids = models.TextField()  # Stores comma-separated result IDs
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vicell_report'