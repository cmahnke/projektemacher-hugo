import os
import subprocess
import yaml
import argparse
import logging

def run_command(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        logging.error(f"Error in '{cmd}':\n{result.stderr.strip()}")
        return False
    return True

def process_config(config, default_repo, prefix="", run_build=False):
    suffix = config.get('suffix', 'custom')
    base_repo = config.get('repo', default_repo)
    tag = config.get('tag')
    prs = config.get('prs', [])
    patches = config.get('patches', [])

    if prefix != "":
        prefix = f"{prefix}-"
    target_dir = f"{prefix}{suffix}"
    logging.info(f"--- Processing: {target_dir} ---")

    if not run_command(f"git clone {base_repo} {target_dir}"):
        return

    if tag:
        logging.info(f"Checking out tag {tag}...")
        run_command(f"git checkout tags/{tag} -b branch-{suffix}", cwd=target_dir)

    for pr in prs:
        logging.info(f"Applying PR #{pr}...")
        if run_command(f"git fetch origin pull/{pr}/head:pr-{pr}", cwd=target_dir):
            run_command(f"git merge pr-{pr} --no-edit", cwd=target_dir)

    if patches:
        for patch_path in patches:
            # Resolve absolute path since we change directory to target_dir
            abs_patch_path = os.path.abspath(patch_path)
            if os.path.exists(abs_patch_path):
                logging.info(f"Applying patch: {patch_path}...")
                run_command(f"git apply {abs_patch_path}", cwd=target_dir)
            else:
                logging.warning(f"Patch file not found at {abs_patch_path}")

    if run_build:
        build_cmd = config.get('build')
        if build_cmd:
            logging.info(f"Running build command: {build_cmd}")
            run_command(build_cmd, cwd=target_dir)
        else:
            logging.warning(f"No build command defined for {target_dir}")

    logging.info(f"Setup complete in ./{target_dir}")

def main():
    parser = argparse.ArgumentParser(description="Build custom repos from YAML config.")
    parser.add_argument("-c", "--config", default="config.yml", help="Path to the YAML configuration file")
    parser.add_argument("-b", "--build", action="store_true", help="Execute the build command if defined")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

    try:
        with open(args.config, 'r') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Failed to read YAML: {e}")
        return

    default_repo = data.get('default-repo')
    prefix = data.get('prefix', "")
    configs = data.get('configs', [])

    for cfg in configs:
        process_config(cfg, default_repo, prefix=prefix, run_build=args.build)

if __name__ == "__main__":
    main()
