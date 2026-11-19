import os
import shutil
import sqlite3
import tempfile
import unittest

import solution


def connect(path):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


class BankTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "bank.db")
        self.conn = connect(self.path)
        solution.create_schema(self.conn)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        shutil.rmtree(self.dir)

    def seed(self):
        with self.conn:
            self.conn.executemany(
                "INSERT INTO users (id, email, name) VALUES (?, ?, ?)",
                [(1, "ada@example.com", "Ada"), (2, "grace@example.com", "Grace")],
            )
            self.conn.executemany(
                "INSERT INTO accounts (id, user_id, balance) VALUES (?, ?, ?)",
                [(10, 1, 500), (11, 1, 20), (20, 2, 100)],
            )

    def balances(self, conn=None):
        conn = conn or self.conn
        return dict(conn.execute("SELECT id, balance FROM accounts").fetchall())

    def transfers(self, conn=None):
        conn = conn or self.conn
        return conn.execute("SELECT from_account, to_account, amount FROM transfers ORDER BY id").fetchall()

    def rejects(self, sql, params=()):
        with self.assertRaises(sqlite3.IntegrityError, msg=sql):
            with self.conn:
                self.conn.execute(sql, params)


class SchemaTest(BankTest):
    def test_columns(self):
        """creates the three tables with the right columns"""
        self.seed()
        with self.conn:
            self.conn.execute(
                "INSERT INTO transfers (id, from_account, to_account, amount, created_at) VALUES (1, 10, 20, 5, '2024-01-01T09:00')"
            )
        self.assertEqual(self.transfers(), [(10, 20, 5)])

    def test_constraints(self):
        """lets the database reject bad data"""
        self.seed()
        self.rejects("INSERT INTO users (id, email, name) VALUES (3, 'ada@example.com', 'Imposter')")
        self.rejects("INSERT INTO users (id, email, name) VALUES (3, NULL, 'No Email')")
        self.rejects("INSERT INTO accounts (id, user_id, balance) VALUES (30, 99, 0)")
        self.rejects("INSERT INTO accounts (id, user_id, balance) VALUES (30, NULL, 0)")
        self.rejects("INSERT INTO accounts (id, user_id, balance) VALUES (30, 1, -1)")
        self.rejects("UPDATE accounts SET balance = balance - 1000 WHERE id = 10")
        self.rejects("INSERT INTO transfers (from_account, to_account, amount, created_at) VALUES (10, 99, 5, 't')")
        self.rejects("INSERT INTO transfers (from_account, to_account, amount, created_at) VALUES (10, 20, 0, 't')")
        self.rejects("INSERT INTO transfers (from_account, to_account, amount, created_at) VALUES (10, 20, 5, NULL)")
        self.assertEqual(self.balances(), {10: 500, 11: 20, 20: 100})


class IndexTest(BankTest):
    def setUp(self):
        super().setUp()
        solution.add_indexes(self.conn)
        self.conn.commit()

    def plan(self, sql):
        return " | ".join(row[3] for row in self.conn.execute("EXPLAIN QUERY PLAN " + sql, (1,)))

    def test_lookup_by_user(self):
        """finds a user's accounts with an index, not a table scan"""
        plan = self.plan("SELECT * FROM accounts WHERE user_id = ?")
        self.assertIn("INDEX", plan, plan)
        self.assertNotIn("SCAN", plan, plan)

    def test_recent_transfers(self):
        """finds a sender's latest transfers already sorted"""
        plan = self.plan("SELECT * FROM transfers WHERE from_account = ? ORDER BY created_at DESC LIMIT 10")
        self.assertIn("INDEX", plan, plan)
        self.assertNotIn("SCAN", plan, plan)
        self.assertNotIn("TEMP B-TREE", plan, f"the index should already be in created_at order: {plan}")

    def test_unique_email(self):
        """looks up users by email using the UNIQUE constraint's index"""
        plan = self.plan("SELECT * FROM users WHERE email = ?")
        self.assertNotIn("SCAN", plan, plan)

    def test_few_indexes(self):
        """adds no more indexes than the queries need"""
        n = self.conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type = 'index' AND sql IS NOT NULL").fetchone()[0]
        self.assertLessEqual(n, 3, "every index slows down every write to its table")


class TransferTest(BankTest):
    def setUp(self):
        super().setUp()
        self.seed()

    def test_moves_money(self):
        """moves money, records the transfer, and commits"""
        solution.transfer(self.conn, 10, 20, 150, "2024-01-01T09:00")
        self.assertFalse(self.conn.in_transaction, "commit when the transfer is done")
        other = connect(self.path)
        try:
            self.assertEqual(self.balances(other), {10: 350, 11: 20, 20: 250}, "another connection sees the committed transfer")
            self.assertEqual(self.transfers(other), [(10, 20, 150)])
        finally:
            other.close()

    def test_insufficient_funds(self):
        """rolls back completely when the balance would go negative"""
        with self.assertRaises(sqlite3.IntegrityError):
            solution.transfer(self.conn, 11, 20, 21, "t")
        self.assertFalse(self.conn.in_transaction, "roll back after a failure")
        self.assertEqual(self.balances(), {10: 500, 11: 20, 20: 100})
        self.assertEqual(self.transfers(), [])

    def test_missing_target(self):
        """rolls back the debit when the target account doesn't exist"""
        with self.assertRaises(ValueError):
            solution.transfer(self.conn, 10, 99, 50, "t")
        self.assertFalse(self.conn.in_transaction, "roll back after a failure")
        other = connect(self.path)
        try:
            self.assertEqual(self.balances(other), {10: 500, 11: 20, 20: 100}, "the money vanished from account 10")
        finally:
            other.close()
        self.assertEqual(self.balances(), {10: 500, 11: 20, 20: 100})

    def test_missing_source(self):
        """refuses to credit money that came from nowhere"""
        with self.assertRaises(ValueError):
            solution.transfer(self.conn, 98, 20, 50, "t")
        self.assertEqual(self.balances(), {10: 500, 11: 20, 20: 100})

    def test_last_step_fails(self):
        """rolls back both updates when recording the transfer fails"""
        with self.assertRaises(sqlite3.IntegrityError):
            solution.transfer(self.conn, 10, 20, -5, "t")  # violates amount > 0
        self.assertFalse(self.conn.in_transaction)
        self.assertEqual(self.balances(), {10: 500, 11: 20, 20: 100})
        self.assertEqual(self.transfers(), [])

    def test_many_transfers(self):
        """keeps the total balance constant across many transfers"""
        moves = [(10, 20, 60), (20, 11, 30), (11, 10, 100), (10, 99, 1), (20, 10, 500), (11, 20, 10)]
        for source, target, amount in moves:
            try:
                solution.transfer(self.conn, source, target, amount, "t")
            except (ValueError, sqlite3.IntegrityError):
                pass
        self.assertEqual(sum(self.balances().values()), 620)
        self.assertEqual(self.transfers(), [(10, 20, 60), (20, 11, 30), (11, 20, 10)])


class DocumentTest(BankTest):
    def test_user_document(self):
        """assembles a user and their accounts into one document"""
        self.seed()
        self.assertEqual(
            solution.user_document(self.conn, 1),
            {"id": 1, "name": "Ada", "email": "ada@example.com", "accounts": [{"id": 10, "balance": 500}, {"id": 11, "balance": 20}]},
        )
        with self.conn:
            self.conn.execute("INSERT INTO users (id, email, name) VALUES (3, 'linus@example.com', 'Linus')")
        self.assertEqual(solution.user_document(self.conn, 3)["accounts"], [])
        self.assertIsNone(solution.user_document(self.conn, 99))


class BTreeTest(unittest.TestCase):
    def test_height(self):
        """B-trees stay shallow even for billions of rows"""
        self.assertEqual(solution.btree_height(1, 100), 1)
        self.assertEqual(solution.btree_height(100, 100), 1)
        self.assertEqual(solution.btree_height(101, 100), 2)
        self.assertEqual(solution.btree_height(1_000_000, 100), 3)
        self.assertEqual(solution.btree_height(1_000_001, 100), 4)
        self.assertEqual(solution.btree_height(1_000_000_000, 500), 4)


if __name__ == "__main__":
    unittest.main()
