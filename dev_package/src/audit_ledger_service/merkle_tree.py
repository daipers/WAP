"""
merkle_tree.py
==============

Merkle tree implementation for aggregating daily audit events.
Provides efficient root hash computation and inclusion proof generation.

Reference: Plan 05-03-PLAN.md - Merkle tree aggregation for audit logs
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class MerkleNode:
    """Represents a node in the Merkle tree."""

    hash: str
    left: Optional[MerkleNode] = None
    right: Optional[MerkleNode] = None
    is_leaf: bool = False
    data: Optional[str] = None  # Original data for leaf nodes


@dataclass
class MerkleProof:
    """Merkle inclusion proof for a leaf node."""

    leaf_hash: str
    root_hash: str
    proof: List[Tuple[str, bool]]  # List of (hash, is_left_sibling)
    verified: bool = False


class MerkleTree:
    """
    Merkle tree for audit log aggregation.

    Builds a binary hash tree from audit events, providing:
    - Efficient root hash computation
    - Inclusion proofs for specific events
    - Tamper-evident aggregation
    """

    # Empty hash for padding odd-length levels
    _empty_hash: str = hashlib.sha256(b"empty").hexdigest()

    def __init__(self):
        self.leaves: List[MerkleNode] = []
        self.root: Optional[MerkleNode] = None
        self._levels: List[List[MerkleNode]] = []

    @staticmethod
    def hash_pair(left_hash: str, right_hash: str) -> str:
        """
        Hash two child hashes together deterministically.

        Args:
            left_hash: Hash of left child
            right_hash: Hash of right child

        Returns:
            Combined hash of both children
        """
        # Sort keys for deterministic serialization
        combined = json.dumps([left_hash, right_hash], sort_keys=True)
        return hashlib.sha256(combined.encode()).hexdigest()

    @staticmethod
    def hash_data(data: str) -> str:
        """Hash a data item to create a leaf node."""
        return hashlib.sha256(data.encode()).hexdigest()

    @classmethod
    def build(cls, data_items: List[str]) -> "MerkleTree":
        """
        Build Merkle tree from list of data items.

        Args:
            data_items: List of strings to aggregate

        Returns:
            MerkleTree instance with root computed
        """
        tree = cls()

        if not data_items:
            # Return empty tree
            return tree

        # Create leaf nodes from data items
        tree.leaves = [
            MerkleNode(hash=cls.hash_data(item), is_leaf=True, data=item)
            for item in data_items
        ]

        # Build tree bottom-up
        current_level = tree.leaves
        tree._levels.append(current_level)

        while len(current_level) > 1:
            next_level = []

            for i in range(0, len(current_level), 2):
                left = current_level[i]
                # Duplicate right node if odd number (self-pairs)
                right = current_level[i + 1] if i + 1 < len(current_level) else left

                parent_hash = cls.hash_pair(left.hash, right.hash)
                parent = MerkleNode(
                    hash=parent_hash, left=left, right=right, is_leaf=False
                )
                next_level.append(parent)

            current_level = next_level
            tree._levels.append(current_level)

        tree.root = current_level[0] if current_level else None
        return tree

    @classmethod
    def build_from_entries(cls, entries: List[dict]) -> "MerkleTree":
        """
        Build Merkle tree from ledger entries.

        Args:
            entries: List of LedgerEntry dictionaries

        Returns:
            MerkleTree instance
        """
        # Serialize entries to deterministic JSON strings
        data_items = [json.dumps(entry, sort_keys=True) for entry in entries]
        return cls.build(data_items)

    def get_root_hash(self) -> str:
        """
        Get root hash for storage/anchoring.

        Returns:
            Root hash string, or empty hash if tree is empty
        """
        if self.root:
            return self.root.hash
        return self._empty_hash

    def prove_inclusion(self, leaf_index: int) -> Optional[MerkleProof]:
        """
        Generate merkle proof for a leaf at given index.

        Args:
            leaf_index: Index of the leaf to prove

        Returns:
            MerkleProof if leaf exists, None otherwise
        """
        if leaf_index >= len(self.leaves) or not self.root:
            return None

        leaf = self.leaves[leaf_index]
        proof_data: List[Tuple[str, bool]] = []

        # Navigate from leaf to root, collecting sibling hashes
        current_idx = leaf_index

        for level_idx in range(len(self._levels) - 1):
            level = self._levels[level_idx]
            is_left_sibling = current_idx % 2 == 0

            if is_left_sibling:
                # Left node - sibling is to the right
                if current_idx + 1 < len(level):
                    sibling_hash = level[current_idx + 1].hash
                    proof_data.append((sibling_hash, False))  # Right sibling
                else:
                    # No sibling (self-pairing case)
                    proof_data.append((level[current_idx].hash, False))
            else:
                # Right node - sibling is to the left
                sibling_hash = level[current_idx - 1].hash
                proof_data.append((sibling_hash, True))  # Left sibling

            # Move to parent level
            current_idx = current_idx // 2

        return MerkleProof(
            leaf_hash=leaf.hash,
            root_hash=self.root.hash,
            proof=proof_data,
            verified=False,
        )

    @staticmethod
    def verify_proof(proof: MerkleProof) -> bool:
        """
        Verify a Merkle inclusion proof.

        Args:
            proof: The proof to verify

        Returns:
            True if proof is valid, False otherwise
        """
        current_hash = proof.leaf_hash

        for sibling_hash, is_left in proof.proof:
            if is_left:
                # Sibling is left child
                current_hash = MerkleTree.hash_pair(sibling_hash, current_hash)
            else:
                # Sibling is right child
                current_hash = MerkleTree.hash_pair(current_hash, sibling_hash)

        proof.verified = current_hash == proof.root_hash
        return proof.verified

    def to_dict(self) -> dict:
        """Serialize tree to dictionary."""
        return {
            "root_hash": self.get_root_hash(),
            "leaf_count": len(self.leaves),
            "tree_height": len(self._levels) if self._levels else 0,
        }
