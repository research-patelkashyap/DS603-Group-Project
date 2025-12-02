import sys, argparse

from vc import VersionControl

def main():
    parser = argparse.ArgumentParser(
        prog="VC2", 
        description="A simple version control system"
    )
    
    subparsers = parser.add_subparsers(
        dest="command", 
        help="Available commands"
    )
    
    # init
    init_parser = subparsers.add_parser(
        "init", 
        help="Initialize a new vc repository"
    )
    
    # add
    add_parser = subparsers.add_parser(
        "add",
        help="Add files and directories to the staging area"
    )
    add_parser.add_argument(
        "paths", 
        nargs="+",
        help="Files and directories to add"
    )
    
    # rm
    remove_parser = subparsers.add_parser("rm", help="Removes or deletes file from version control.")
    remove_parser.add_argument(
        "paths",
        nargs="+",
        help="Files to be deleted"
    )
    
    # commit
    commit_parser = subparsers.add_parser("commit", help="Create a new commit.")
    commit_parser.add_argument("-m", "--message", help="Commit message", required=True)
    commit_parser.add_argument("--author_name", help="Author name")
    commit_parser.add_argument("--author_email", help="Author email")
    
    # branch
    branch_parser = subparsers.add_parser("branch", help="Create a new branch or checkout to an existing branch.")
    branch_parser.add_argument("-n", "--branch_name", help="Name to create a new branch.")
    
    # checkout
    checkout_parser = subparsers.add_parser("checkout", help="Checkout a commit or branch.")
    checkout_parser.add_argument("target", help="Commit hash or branch name.")
    
    # log
    log_parser = subparsers.add_parser("log", help="Logs commit list.")
    
    # status
    status_parser = subparsers.add_parser(
        "status",
        help="Show working tree, staged, modified, and untracked files."
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    vc_repository = VersionControl()
    
    try:
        if args.command == 'init':
            if not vc_repository.init():
                print('VC Repository already exists')
                return
        
        elif args.command == 'add':
            if not vc_repository.vc_dir_path.exists():
                print('VC Repository already exists')
                return
            
            for path in args.paths:
                vc_repository.add(path)
                
        elif args.command == 'rm':
            if not vc_repository.vc_dir_path.exists():
                print('VC Repository already exists')
                return
            
            for path in args.paths:
                vc_repository.rm(path)
                
        elif args.command == 'commit':
            if not vc_repository.vc_dir_path.exists():
                print('VC Repository already exists')
                return
            
            author = args.author_name or ''
            email = args.author_email or ''
            vc_repository.commit(args.message, author, email)
                
        elif args.command == "branch":
            if not vc_repository.vc_dir_path.exists():
                print('VC Repository already exists')
                return
            
            if args.branch_name:
                vc_repository.branch(args.branch_name)

            else:
                vc_repository.list_branches()
        
        elif args.command == "checkout":
            if not vc_repository.vc_dir_path.exists():
                print('VC Repository already exists')
                return

            elif args.target in vc_repository.get_branches():
                vc_repository.checkout_branch(args.target)

            else:
                vc_repository.checkout_commit(args.target)

        elif args.command == 'log':
            if not vc_repository.vc_dir_path.exists():
                print('VC Repository already exists')
                return
            
            vc_repository.log()
            
        elif args.command == 'status':
            if not vc_repository.vc_dir_path.exists():
                print('VC Repository already exists')
                return
            
            vc_repository.status()
            
    except Exception as e:
        print(f'VC Error: {e}')
        sys.exit(1)
    
main()
