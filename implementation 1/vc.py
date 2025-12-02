import os, json, hashlib, zlib
from pathlib import Path

from blob import Blob

class VersionControl:
    def __init__(self):
        self.path = Path('.').resolve()
        self.vc_dir_path = self.path / '.vc'
        self.blob_path = self.vc_dir_path / 'blobs'
        self.commit_tree_path = self.vc_dir_path / 'commit_tree'
        
        self.stage_path = self.vc_dir_path / 'stage.json'
        self.commit_list = self.vc_dir_path / 'commit_list.json'
        self.index = self.vc_dir_path / 'index.json'

    def init(self) -> bool:
        if self.vc_dir_path.exists():
            return False
        

        os.mkdir(self.vc_dir_path)
        os.mkdir(self.blob_path)
        os.mkdir(self.commit_tree_path)

        with open(self.stage_path, "w") as f:
            json.dump({}, f, indent=4)
        with open(self.commit_list, "w") as f:
            json.dump({}, f, indent=4)
        with open(self.index, "w") as f:
            json.dump(
                {
                    "current_branch": "master",
                    "current_commit": "",
                    "branches": { "master": "" },
                    "current_snapshot": {}
                },
                f,
                indent=4
            )
        
        print(f'Initialized version control directory in {self.vc_dir_path}')
            
        return True
    

    def load_stage(self) -> any:
        if os.path.exists(self.stage_path):
            with open(self.stage_path, "r") as f:
                return json.load(f)

        return {}


    def save_stage(self, stage_tree) -> None:
        with open(self.stage_path, "w") as f:
            json.dump(stage_tree, f, indent=4)


    def insert_stage(self, path: str, hash: str) -> None:
        index = self.load_stage()
        
        if not isinstance(path, str):
            path = path.as_posix()

        parts = path.split("/")
        curr = index

        for part in parts[:-1]:
            curr = curr.setdefault(part, {})

        curr[parts[-1]] = hash
        
        self.save_stage(index)


    def store_blob(self, blob: Blob) -> bool:
        hash = blob.hash
        
        blob_file_path = self.blob_path / hash
        
        if not blob_file_path.exists():
            content = zlib.compress(blob.content)
            blob_file_path.write_bytes(content)
            
            return True

        return False
 

    def add_file(self, file_to_add) -> None:
        content = file_to_add.read_bytes()
        
        blob = Blob(content)

        if self.store_blob(blob):
            hash = blob.hash
            rel_path = file_to_add.relative_to(self.path).as_posix()
            self.insert_stage(rel_path, hash)
            
            print(f"+ File: {file_to_add}")    
        
        else:
            print(f"File: {file_to_add} is already added.")


    def add_dir(self, dir_to_add) -> None:
        for path in dir_to_add.rglob("*"):
            if path.is_file():
                self.add_file(path)


    # add
    def add(self, path_to_add: str) -> None:
        path_to_add = self.path / path_to_add
        
        if not path_to_add.exists():
            raise FileNotFoundError(f"Path {path_to_add} does not exists.")
        
        if path_to_add.is_file():
            self.add_file(path_to_add)

        elif path_to_add.is_dir():
            self.add_dir(path_to_add)

        else:
            raise ValueError(f"{path_to_add} is neither a file nor a directory.")


    def build_snapshot(self, commits, commit_hash):
        snapshot = {}
        chain = []
        cur = commit_hash
        while cur:
            chain.append(cur)
            cur = commits[cur]["parent"]

        chain.reverse()

        for cid in chain:
            tree_hash = commits[cid]["tree"]
            tree_file = self.commit_tree_path / f"{tree_hash}.json"
            if tree_file.exists():
                subtree = json.loads(tree_file.read_text())
                self.deep_merge(snapshot, subtree)

        return snapshot
    
    
    def deep_merge(self, base, new):
        for key, val in new.items():
            if val == "__deleted__":
                if key in base:
                    del base[key]
                continue
        
            if isinstance(val, dict):
                base[key] = self.deep_merge(base.get(key, {}), val)
            else:
                base[key] = val
        return base


    # commit
    def commit(self, message: str, author: str, email: str) -> None:
        stage = self.load_stage()
        
        if not stage:
            print("Nothing to commit.")
            return
        
        stage_bytes = json.dumps(stage, sort_keys=True).encode()
        
        tree_hash = hashlib.sha1(stage_bytes).hexdigest()
        
        tree_path = self.commit_tree_path / f"{tree_hash}.json"
        if not tree_path.exists():
            with open(tree_path, "w") as f:
                json.dump(stage, f, indent=4)

        if self.commit_list.exists():
            commits = json.loads(self.commit_list.read_text())
        else:
            commits = {}

        head = json.loads(self.index.read_text()) if self.index.exists() else {
            "current_commit": "",
            "current_snapshot": {}
        }
        
        parent_commit = head.get("current_commit", "")
        
        commit_obj = {
            "tree": tree_hash,
            "parent": parent_commit,
            "message": message,
            "author": author,
            "email": email
        }
        
        commit_bytes = json.dumps(commit_obj, sort_keys=True).encode()
        commit_hash = hashlib.sha1(commit_bytes).hexdigest()
        
        commits[commit_hash] = commit_obj
        with open(self.commit_list, "w") as f:
            json.dump(commits, f, indent=4)
        
        new_snapshot = self.build_snapshot(commits, commit_hash)
        
        current_branch = head.get("current_branch")
        if current_branch:
            branches = head.get("branches", {})
            branches[current_branch] = commit_hash
            head["branches"] = branches
        
        head["current_commit"] = commit_hash
        head["current_snapshot"] = new_snapshot
        
        with open(self.index, "w") as f:
            json.dump(head, f, indent=4)

        self.save_stage({})

        print(f"[{commit_hash[:7]}] {message}")

    
    # rm
    def rm(self, path: str):
        file_path = (self.path / path).resolve()

        if not file_path.exists():
            raise FileNotFoundError(f"{path} does not exist.")

        rel_path = file_path.relative_to(self.path).as_posix()
        
        file_path.unlink()
        print(f"Removed file: {path}")

        self.insert_stage(rel_path, "__deleted__")

        print(f"- Deleted: {path}")
    
        
    # branch
    def branch(self, name: str) -> None:
        if not self.index.exists():
            print("Repository not initialized.")
            return

        head = json.loads(self.index.read_text())
        current_commit = head["current_commit"]

        branches = head.get("branches", {})
        
        if name in branches:
            print(f"Branch '{name}' already exists.")
            return

        branches[name] = current_commit
        head["branches"] = branches

        with open(self.index, "w") as f:
            json.dump(head, f, indent=4)

        print(f"Branch '{name}' created at {current_commit}")
    
    
    def list_branches(self) -> None:
        head = json.loads(self.index.read_text())
        branches = head.get("branches", {})
        current = head.get("current_branch")

        for br in branches:
            star = "*" if br == current else " "
            print(f"{star} {br}")
    
    
    def restore_from_snapshot(self, tree: dict, root: Path):
        for name, val in tree.items():
            dest = root / name

            if isinstance(val, dict):
                dest.mkdir(exist_ok=True)
                self.restore_from_snapshot(val, dest)
            else:
                blob_path = self.blob_path / val
                content = zlib.decompress(blob_path.read_bytes())
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(content)


    def clear_working_directory(self):
        for path in self.path.rglob("*"):
            if ".vc" in path.parts:
                continue

            if path.is_file():
                path.unlink()
            elif path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    pass
    

    def get_branches(self):
        if not self.index.exists():
            return []

        head = json.loads(self.index.read_text())
        branches = head.get("branches", {})

        return list(branches.keys())
    
    
    # checkout branch
    def checkout_branch(self, name: str):
        head = json.loads(self.index.read_text())
        branches = head.get("branches", {})

        if name not in branches:
            print(f"Branch '{name}' does not exist.")
            return

        commit_hash = branches[name]

        commits = json.loads(self.commit_list.read_text())

        snapshot = self.build_snapshot(commits, commit_hash)

        self.clear_working_directory()
        self.restore_from_snapshot(snapshot, self.path)

        head["current_branch"] = name
        head["current_commit"] = commit_hash
        head["current_snapshot"] = snapshot

        with open(self.index, "w") as f:
            json.dump(head, f, indent=4)

        print(f"Switched to branch '{name}'")
    
    
    # checkout commit
    def checkout_commit(self, commit_hash: str):
        commits = json.loads(self.commit_list.read_text())

        if commit_hash not in commits:
            print(f"Commit '{commit_hash}' does not exist.")
            return

        snapshot = self.build_snapshot(commits, commit_hash)

        self.clear_working_directory()
        self.restore_from_snapshot(snapshot, self.path)

        head = json.loads(self.index.read_text())

        branch_attached = None
        for br, h in head.get("branches", {}).items():
            if h == commit_hash:
                branch_attached = br
                break

        head["current_branch"] = branch_attached
        head["current_commit"] = commit_hash
        head["current_snapshot"] = snapshot

        with open(self.index, "w") as f:
            json.dump(head, f, indent=4)

        if branch_attached:
            print(f"Switched to branch '{branch_attached}'")
        else:
            print(f"HEAD is now at {commit_hash[:7]} (detached)")

    
    # log
    def log(self) -> None:
        if not self.commit_list.exists():
            print("No commits.")
            return

        commits = json.loads(self.commit_list.read_text())
        head = json.loads(self.index.read_text())
        cur = head.get("current_commit", "")

        if not cur:
            print("No commits yet.")
            return

        while cur:
            c = commits[cur]
            print("------------------------------")
            print(f"commit {cur}")
            print(f"Tree: {c['tree']}")
            print(f"Message: {c['message']}")
            print(f"Author: {c['author']}")
            print(f"Email: {c['email']}")
            cur = c["parent"]

    
    def _flatten_tree(self, tree, prefix=""):
        paths = []
        for key, val in tree.items():
            new = f"{prefix}/{key}" if prefix else key
            if isinstance(val, dict):
                paths.extend(self._flatten_tree(val, new))
            else:
                paths.append(new)
        return paths
    
    
    def _list_working_files(self):
        files = []
        for p in self.path.rglob("*"):
            if ".vc" in p.parts:
                continue
            if p.is_file():
                files.append(p.relative_to(self.path).as_posix())
        return files
    
    
    def _is_deleted(self, staged_tree, file_path):
        parts = file_path.split("/")
        curr = staged_tree
        for p in parts[:-1]:
            if p not in curr:
                return False
            curr = curr[p]
        return curr.get(parts[-1]) == "__deleted__"
    
    
    def _get_hash_from_snapshot(self, tree, rel_path):
        parts = rel_path.split("/")
        curr = tree

        for p in parts[:-1]:
            if p not in curr:
                return None
            curr = curr[p]

        return curr.get(parts[-1])
    
    
    # status
    def status(self):
        head = json.loads(self.index.read_text())
        snapshot = head.get("current_snapshot", {})
        staged = self.load_stage()

        staged_flat = set(self._flatten_tree(staged))
        snapshot_flat = set(self._flatten_tree(snapshot))
        working_files = set(self._list_working_files())

        print("\nChanges to be committed")
        if staged_flat:
            for p in staged_flat:
                if staged and self._is_deleted(staged, p):
                    print(f"deleted: {p}")
                else:
                    print(f"modified/added: {p}")
        else:
            print("(nothing to commit)")


        print("\nChanges not staged for commit")
        modified = []
        deleted = []

        for path in snapshot_flat:
            if path not in working_files and path not in staged_flat:
                deleted.append(path)
            else:
                if path in working_files:
                    snap_hash = self._get_hash_from_snapshot(snapshot, path)
                    blob_path = self.blob_path / snap_hash
                    old_content = zlib.decompress(blob_path.read_bytes())
                    new_content = (self.path / path).read_bytes()

                    if old_content != new_content and path not in staged_flat:
                        modified.append(path)

        if modified or deleted:
            for p in modified:
                print(f"modified: {p}")
            for p in deleted:
                print(f"deleted: {p}")
        else:
            print("(no changes)")


        print("\nUntracked files")
        untracked = working_files - snapshot_flat - staged_flat
        if untracked:
            for p in untracked:
                print(f"{p}")
        else:
            print("(none)")
        
        print()
