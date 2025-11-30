# DS603 Group Project

## Team Members

* 202518008: Devam Gandhi
* 202518025: Jay Patel
* 202518036: Kashyap Patel

## Problem Statement and Objective

Modern software development requires efficient mechanisms to track changes, manage versions, handle branching, and recover previous states of a project. Traditional Version Control Systems (VCS) such as Git rely on a structured object database and a directed acyclic graph (DAG) of commits to ensure robustness, scalability, and immutability.

The objective of this work is to design and implement two custom version control systems inspired by Git. Both systems support essential functionalities such as:

* Tracking file changes
* Staging and committing
* Managing branches
* Checking out commits or branches
* Viewing history
* Viewing file status

However, the two implementations differ fundamentally in how they manage internal data structures and store repository metadata.

**Goals:**

1. Implement a functional VCS with core Git-like commands.
2. Explore two alternative designs and compare their performance.
3. Analyze technical trade-offs between JSON-based snapshot merging and Git-style object storage.
4. Provide a formal understanding of key operations and their computational complexity.

## Implementations

Below is a structured explanation of both systems.

### Implementation 1

This is a simpler, higher-level version control system that uses **JSON files**, hierarchical dictionaries, and file hashes to track changes.

#### Key Characteristics

* Uses `.vc/stage.json` for staging changes.
* Stores commit trees as JSON files in `.vc/commit_tree/`.
* Merges snapshots using nested dictionary merge operations.
* Tracks deletions explicitly using `"__deleted__"` markers.
* Stores file contents as compressed blob objects.

#### Internal Components

* **stage.json** — holds the staged file tree.

* **commit_list.json** — list of commits with metadata (`tree`, `parent`, `message`, etc.).

* **index.json** — contains:

  * current branch
  * current commit hash
  * snapshot of last applied commit
  * mapping of branches to latest commit

* **blobs/** — stores compressed file contents.

* **commit_tree/** — stores JSON-formatted commit trees.

#### Operational Flow

1. **Add:**
   * Hash file content, store blob, update `stage.json`.

2. **Commit:**
   * Convert stage -> snapshot
   * Merge with previous snapshots
   * Write commit metadata to `commit_list.json`.

3. **Branch Management:**
   * Maintain branch pointers inside `index.json`.

4. **Checkout:**
   * Rebuild snapshot from commit chain
   * Restore files from snapshot

5. **Status:**
   * Compare working directory, stage, and snapshot.

#### Strengths

* Simple to implement, easy to debug.
* Good for understanding VCS fundamentals.

#### Limitations

* JSON tree merges scale poorly on large repositories.
* Requires full-snapshot reconstruction on checkout.
* Lacks object-level deduplication beyond blobs.

### Implementation 2

This version control system closely follows the internal design of Git, including **blob**, **tree**, and **commit** objects stored in a structured object database.

#### Key Characteristics

* Stores content-addressed objects in `.vc/objects/aa/bbcd…`
* Uses Git-like structures:
  * Blob objects
  * Tree objects
  * Commit objects
* Uses a real **object graph (DAG)** instead of complete snapshots.
* Maintains branches via `.vc/refs/heads/branch_name`.
* HEAD pointer behaves similarly to Git.

#### Internal Components

* **objects/** — all versioned content stored as immutable objects.
* **refs/heads/** — branch pointers to commit hashes.
* **HEAD** — pointer to current branch.
* **index** — staging area mapping file paths -> blob hashes.
* **VCObject / Blob / Tree / Commit classes** — structured object types with serialization and hashing.

#### Operational Flow

1. **Add:**
   * Hash file -> create Blob object -> store in object database.
   * Update index mapping.

2. **Commit:**
   * Create Tree object recursively reflecting file hierarchy.
   * Create Commit object pointing to tree + parent commit.
   * Update branch pointer.
   * Clear index.

3. **Checkout:**
   * Set HEAD to branch.
   * Reconstruct working directory from tree objects.
   * Clear index.

4. **Branch:**
   * Simple creation of a new reference under `refs/heads/`.

5. **Log:**
   * Walk the commit chain via parent pointers.

6. **Status:**
   * Compare working directory -> index -> last commit snapshot.

#### Strengths

* Exactly models Git’s lightweight object storage.
* Efficient for large repositories.
* Checkout is fast: retrieves only needed blobs via tree hierarchy.
* No JSON snapshot merging needed.

#### Limitations

* More complex to implement (serialization, tree recursion).
* Requires clean abstraction for objects.

## Report

Complexities are in terms of:
* F = number of files
* s = average file size
* D = number of directories
* C = number of commits
* B = number of branches

| Operation | Implementation 1 (JSON-Based) – Time | Implementation 2 (Git-Like Objects) – Time | Implementation 1 – Space | Implementation 2 – Space | Notes |
|----------|----------------------------------------|----------------------------------------------|----------------------------|---------------------------|-------|
| init | O(1) | O(1) | O(1) | O(1) | Create fixed folders/files |
| add(file) | O(s) | O(s) | O(s) per blob | O(s) per blob | Hash and store content |
| add(dir) | O(F·s) | O(F·s) | O(F·s) | O(F·s) | Walk directory recursively |
| store blob | O(s) | O(s) | O(s) | O(s) | Compression/serialization |
| create tree | O(F) | O(F log F) | O(F) | O(F) | Git sorts entries → log F |
| commit | O(F) | O(F log F + s) | O(F) | O(F) + O(C) objects | JSON merges vs DAG |
| checkout(branch) | O(F) | O(F + D) | O(F) | O(F) | Git restores only required trees |
| checkout(commit) | O(F) | O(F + D) | O(F) | O(F) | DAG navigation is fast |
| rm | O(1) | O(1) | O(1) | O(1) | Just mark deletion |
| branch(create) | O(1) | O(1) | O(1) | O(1) | Simple reference |
| branch(list) | O(B) | O(B) | O(B) | O(B) | Iterate branch entries |
| log | O(C) | O(C) | O(C) | O(C) | Walk parent pointer chain |
| status | O(F·s) | O(F·s) | O(F) | O(F) | Must hash all working files |

### Summary

| Area                 | JSON-Based VC | Git-Style VC                | Winner    |
| -------------------- | ------------- | --------------------------- | --------- |
| Commit Speed         | Faster        | Slower due to sorting       | JSON      |
| Checkout Speed       | Medium        | Faster for large repos      | Git-style |
| Scalability          | Poor          | Excellent                   | Git-style |
| Space Efficiency     | Poor          | Excellent (deduped objects) | Git-style |
| Snapshot Computation | Linear merge  | DAG-based incremental       | Git-style |
| Code Simplicity      | Simple        | Complex                     | JSON      |
| Real-world usability | Low           | Very High                   | Git-style |
