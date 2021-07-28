# BBAR

The Batch Benchmark Automatic Runner runs batch benchmarks automatically for you!

Simply define your benchmarks in bbar.toml (or some other toml file):

	modules        = ["gcc", "cuda", "openmpi"]
	batchfile_name = "{SBATCH_job-name}-{SBATCH_n}.batch"
	max_procs_per_node = 4

	[sbatch_params]
	job-name  = "benchmark"
	account   = "project_XXXXXXXX"
	time      = "04:00:00"
	mem       = 48000
	partition = "gpu"
	gres      = "gpu:v100:{procs_on_node}"
	output    = "benchmark-{SBATCH_job-name}-{SBATCH_n}.out"

	#Will create benchmarks for 1 to 2^4 processes
	[scaleup]
	start       = 1
	step_factor = 2
	num_steps   = 5

	#Set up separate working directories for each benchmark in your command
	[benchmarks]
	workdir      = "results_{SBATCH_n}/mesh_{arguments[0]}/thresh_{UCX_RNDV_THRESH}"
	num_settings = 10
	command      = "./benchmark"
	arguments    = [256, 256, 256]

	[benchmarks.env_vars]  
	UCX_RNDV_THRESH.start = 4096
	UCX_RNDV_THRESH.step  = 2048

Then generate SLURM batch files and run them all with:

	$bbar run 

## Dependencies

You need at least the `wheel` package from pip

	$pip3 install --user wheel

## Installation

Run the following in the source directory to install a linked source repo:
	
	$make install_source

If you want to build and install a wheel, run:

	$make install_wheel

or if you already have a wheel file, just run:

	$python3 -m wheel install bbar-0.1-py3-none-any.whl
	
## Distribution

To generate the wheel file, run:

	$make build_wheel
	
Or manually:

	$python3 setup.py bdist_wheel
	
This will create the wheel file in  ```bbar/dist```
