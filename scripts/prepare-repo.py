import os
import subprocess
import yaml
import argparse
import logging
import zipfile
import tarfile
import shutil
import json

def run_command(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        logging.error(f"Error in '{cmd}':\n{result.stderr.strip()}")
        return False
    return True

def process_config(config, default_repo, prefix="", run_build=False, archive_name=None):
    suffix = config.get('suffix', 'custom')
    base_repo = config.get('repo', default_repo)
    tag = config.get('tag')
    prs = config.get('prs', [])
    patches = config.get('patches', [])
    config_archive_name = config.get('archive')

    if not archive_name and config_archive_name:
        archive_name = config_archive_name
        run_build = True

    if prefix != "":
        prefix = f"{prefix}-"
    target_dir = f"{prefix}{suffix}"
    logging.info(f"--- Processing: {target_dir} ---")

    if not run_command(f"git clone {base_repo} {target_dir}"):
        return target_dir, None

    if tag and tag != "latest":
        logging.info(f"Checking out tag {tag}...")
        run_command(f"git checkout tags/{tag}", cwd=target_dir)

    for pr in prs:
        logging.info(f"Applying PR #{pr}...")
        if run_command(f"git fetch origin pull/{pr}/head:pr-{pr}", cwd=target_dir):
            run_command(f"git merge pr-{pr} --no-edit", cwd=target_dir)

    if patches:
        for patch_path in patches:
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
            if not run_command(build_cmd, cwd=target_dir):
                logging.error(f"Build failed for {target_dir}. Skipping archive.")
                return target_dir, None
        else:
            logging.warning(f"No build command defined for {target_dir}")

    archive_path = None
    if archive_name:
        logging.info(f"Archiving new files to {archive_name}...")
        res = subprocess.run("git ls-files --others --exclude-standard",
                             shell=True, capture_output=True, text=True, cwd=target_dir)
        new_files = [f for f in res.stdout.splitlines() if f]

        if not new_files:
            logging.warning(f"No new files found in {target_dir} to archive.")
        else:
            try:
                if archive_name.endswith('.zip'):
                    with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for f in new_files:
                            zipf.write(os.path.join(target_dir, f), f)
                elif archive_name.endswith(('.tar', '.tar.gz', '.tgz')):
                    mode = 'w:gz' if archive_name.endswith(('.gz', '.tgz')) else 'w'
                    with tarfile.open(archive_name, mode) as tar:
                        for f in new_files:
                            tar.add(os.path.join(target_dir, f), arcname=f)
                else:
                    logging.error(f"Unsupported archive format: {archive_name}")
                archive_path = os.path.abspath(archive_name)
            except Exception as e:
                logging.error(f"Failed to create archive {archive_name}: {e}")

    logging.info(f"Setup complete in ./{target_dir}")
    return target_dir, archive_path

def main():
    parser = argparse.ArgumentParser(description="Build custom repos from YAML config.")
    parser.add_argument("-c", "--config", default="config.yml", help="Path to the YAML configuration file")
    parser.add_argument("-b", "--build", action="store_true", help="Execute the build command if defined")
    parser.add_argument("-a", "--archive", help="Archive name for new files (implies -b)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("--clean", action="store_true", help="Remove checked out repositories on exit")
    parser.add_argument("--json-output", action="store_true", help="Print created archive paths as JSON")
    args = parser.parse_args()

    if args.archive:
        args.build = True

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

    created_dirs = []
    created_archives = []
    try:
        for cfg in configs:
            target_dir, archive_path = process_config(cfg, default_repo, prefix=prefix, run_build=args.build, archive_name=args.archive)
            if target_dir:
                created_dirs.append(target_dir)
            if archive_path:
                created_archives.append(archive_path)
    finally:
        if args.clean:
            for d in created_dirs:
                if os.path.exists(d):
                    logging.info(f"Cleaning up {d}...")
                    shutil.rmtree(d)

        if args.json_output:
            print(json.dumps(created_archives))

if __name__ == "__main__":
    main()
