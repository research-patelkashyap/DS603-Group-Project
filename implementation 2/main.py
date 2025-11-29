import sys, argparse

from vc import VersionControl

def main():
    parser = argparse.ArgumentParser(prog="VC", description="A simple version control system")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # init
    init_parser = subparsers.add_parser("init", help="Initialize a new vc repository")
    
    # add
    add_parser = subparsers.add_parser(
        "add", help="Add files and directories to the staging area"
    )
    add_parser.add_argument("paths", nargs="+", help="Files and directories to add")
    
    # commit
    commit_parser = subparsers.add_parser("commit", help="Create a new commit")
    commit_parser.add_argument("-m", "--message", help="Commit message", required=True)
    commit_parser.add_argument("--author_name", help="Author name")
    commit_parser.add_argument("--author_email", help="Author email")

    # checkout
    checkout_parser = subparsers.add_parser("checkout", help="Move/Create a new branch")
    checkout_parser.add_argument("branch", help="Branch to switch to")
    checkout_parser.add_argument(
        "-b",
        "--create-branch",
        action="store_true",
        help="Create and switch to a new branch",
    )
    
    # branch
    branch_parser = subparsers.add_parser("branch", help="List or manage branches")
    branch_parser.add_argument("name", nargs="?")
    branch_parser.add_argument(
        "-d",
        "--delete",
        action="store_true",
        help="Delete the branch",
    )
    
    # log
    log_parser = subparsers.add_parser("log", help="Show commit history")
    log_parser.add_argument(
        "-n",
        "--max-count",
        type=int,
        default=10,
        help="Limit commits shown",
    )

    # status
    status_parser = subparsers.add_parser("status", help="Show repository status")
    
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
            if not vc_repository.vc_dir.exists():
                print('Not a VC Repository')
            
            for path in args.paths:
                vc_repository.add(path)
                
        elif args.command == 'commit':
            if not vc_repository.vc_dir.exists():
                print('Not a VC Repository')
            
            author = args.author_name or ''
            email = args.author_email or ''
            vc_repository.commit(args.message, author, email)
            
        elif args.command == 'checkout':
            if not vc_repository.vc_dir.exists():
                print('Not a VC Repository')
             
            vc_repository.checkout(args.branch, args.create_branch)
            
        elif args.command == "branch":
            if not vc_repository.vc_dir.exists():
                print('Not a VC Repository')
            
            vc_repository.branch(args.name, args.delete)
            
        elif args.command == "log":
            if not vc_repository.git_dir.exists():
                print("Not a git repository")
                return

            vc_repository.log(args.max_count)

        elif args.command == "status":
            if not vc_repository.git_dir.exists():
                print("Not a git repository")
                return

            vc_repository.status()

    except Exception as e:
        print(f'VC Error: {e}')
        sys.exit(1)
    
main()
