bbarfile_defaults="""
max_procs_per_node = 4
batchfile_name     = "{SBATCH_job-name}-{SBATCH_n}.batch"
setup		   = ""
cleanup		   = ""
scheduler          = "SLURM"

status_analysis    = "exit_code"

[env_vars]

[sbatch_params]
job-name = "benchmark_job"
output   = "{SBATCH_job-name}-{SBATCH_n}.out"



"""
