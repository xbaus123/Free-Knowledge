import unittest

from solution import delivery_order, dot_stuff, hop_path, mail_domain, parse_reply, reply_action, smtp_commands


class MailDomain(unittest.TestCase):
    def test_plain(self):
        """bob@example.com, as in the reading"""
        self.assertEqual(mail_domain("bob@example.com"), "example.com")

    def test_case(self):
        """Domains are lowercased"""
        self.assertEqual(mail_domain("bob@Example.COM"), "example.com")

    def test_subdomain(self):
        """carol@cs.example.edu, from the check quiz"""
        self.assertEqual(mail_domain("carol@cs.example.edu"), "cs.example.edu")

    def test_display_name(self):
        """A From: header style address"""
        self.assertEqual(mail_domain("Alice Smith <alice@example.org>"), "example.org")

    def test_at_in_display_name(self):
        """Only what's in the angle brackets counts"""
        self.assertEqual(mail_domain('"bob@home" <bob@work.example.com>'), "work.example.com")

    def test_no_at(self):
        """No @, no domain"""
        with self.assertRaises(ValueError):
            mail_domain("postmaster")


class DeliveryOrder(unittest.TestCase):
    def test_reading_example(self):
        """10 first, then the two 20s in their order"""
        mx = ["20 mail2.example.com.", "10 mail1.example.com.", "20 mail3.example.com."]
        self.assertEqual(delivery_order(mx, "example.com"),
                         ["mail1.example.com.", "mail2.example.com.", "mail3.example.com."])

    def test_marshall(self):
        """marshall.edu's single MX at priority 0"""
        self.assertEqual(delivery_order(["0 marshall-edu.mail.protection.outlook.com."], "marshall.edu"),
                         ["marshall-edu.mail.protection.outlook.com."])

    def test_numeric(self):
        """Priorities compare as numbers: 5 before 10, 10 before 100"""
        mx = ["100 c.x.org.", "10 b.x.org.", "5 a.x.org."]
        self.assertEqual(delivery_order(mx, "x.org"), ["a.x.org.", "b.x.org.", "c.x.org."])

    def test_implicit_mx(self):
        """No MX: the domain itself is the mail host"""
        self.assertEqual(delivery_order([], "Example.NET"), ["example.net"])

    def test_null_mx(self):
        """MX 0 . means this domain takes no mail"""
        self.assertEqual(delivery_order(["0 ."], "noreply.example.com"), [])


class DotStuff(unittest.TestCase):
    def test_plain_line(self):
        """An ordinary line is unchanged"""
        self.assertEqual(dot_stuff("Are you free on Friday?"), "Are you free on Friday?")

    def test_leading_dot(self):
        """.hidden file, from the check quiz"""
        self.assertEqual(dot_stuff(".hidden file"), "..hidden file")

    def test_lone_dot(self):
        """A body line that's just a dot must not end the message"""
        self.assertEqual(dot_stuff("."), "..")

    def test_dot_in_middle(self):
        """Only a leading dot counts"""
        self.assertEqual(dot_stuff("example.com"), "example.com")


class SmtpCommands(unittest.TestCase):
    def test_reading_conversation(self):
        """Alice to Bob, as in the Talking SMTP reading"""
        body = ["From: Alice <alice@example.org>", "To: Bob <bob@example.com>", "Subject: Lunch?", "",
                "Are you free on Friday?"]
        self.assertEqual(smtp_commands("mail.example.org", "alice@example.org", ["bob@example.com"], body), [
            "EHLO mail.example.org",
            "MAIL FROM:<alice@example.org>",
            "RCPT TO:<bob@example.com>",
            "DATA",
            "From: Alice <alice@example.org>",
            "To: Bob <bob@example.com>",
            "Subject: Lunch?",
            "",
            "Are you free on Friday?",
            ".",
            "QUIT",
        ])

    def test_several_recipients(self):
        """One RCPT TO per recipient, in order"""
        out = smtp_commands("h", "a@x.org", ["b@y.com", "c@z.net", "d@y.com"], ["hi"])
        self.assertEqual([c for c in out if c.startswith("RCPT")],
                         ["RCPT TO:<b@y.com>", "RCPT TO:<c@z.net>", "RCPT TO:<d@y.com>"])

    def test_dot_stuffed_body(self):
        """Body lines are dot-stuffed; the end-of-message dot is not"""
        out = smtp_commands("h", "a@x.org", ["b@y.com"], [".", ".net"])
        self.assertEqual(out[-5:], ["DATA", "..", "..net", ".", "QUIT"])


class ReplyAction(unittest.TestCase):
    def test_each_class(self):
        """The first digit decides"""
        self.assertEqual(reply_action("250 OK"), "ok")
        self.assertEqual(reply_action("354 Start mail input; end with <CRLF>.<CRLF>"), "continue")
        self.assertEqual(reply_action("451 4.7.1 Please try again later"), "retry")
        self.assertEqual(reply_action("550 5.1.1 User unknown"), "bounce")

    def test_greeting_and_goodbye(self):
        """220 and 221 are both 2xx"""
        self.assertEqual(reply_action("220 mx.example.com ESMTP ready"), "ok")
        self.assertEqual(reply_action("221 Bye"), "ok")

    def test_multiline_piece(self):
        """A dash line still has a code"""
        self.assertEqual(reply_action("250-STARTTLS"), "ok")

    def test_not_a_reply(self):
        """Garbage, or a code outside 2xx to 5xx"""
        for bad in ["hello", "25 OK", "650 What", ""]:
            with self.assertRaises(ValueError):
                reply_action(bad)


class ParseReply(unittest.TestCase):
    def test_ehlo_reply(self):
        """The EHLO reply from the reading"""
        lines = ["250-mx.example.com Hello mail.example.org", "250-SIZE 35882577", "250-STARTTLS", "250 8BITMIME"]
        self.assertEqual(parse_reply(lines),
                         (250, ["mx.example.com Hello mail.example.org", "SIZE 35882577", "STARTTLS", "8BITMIME"]))

    def test_single_line(self):
        """Most replies are one line"""
        self.assertEqual(parse_reply(["221 Bye"]), (221, ["Bye"]))

    def test_code_only(self):
        """A bare code is a complete reply"""
        self.assertEqual(parse_reply(["250"]), (250, [""]))

    def test_unfinished(self):
        """The last line has a dash, so the reply isn't over"""
        with self.assertRaises(ValueError):
            parse_reply(["250-mx.example.com", "250-STARTTLS"])

    def test_ended_early(self):
        """A space before the last line"""
        with self.assertRaises(ValueError):
            parse_reply(["250 mx.example.com", "250 STARTTLS"])

    def test_mixed_codes(self):
        """Every line must have the same code"""
        with self.assertRaises(ValueError):
            parse_reply(["250-mx.example.com", "550 No"])

    def test_empty(self):
        """No lines at all"""
        with self.assertRaises(ValueError):
            parse_reply([])


class HopPath(unittest.TestCase):
    HEADERS = [
        "Return-Path: <alice@example.org>",
        "Received: from mail.example.org (mail.example.org [198.51.100.20]) by mx.example.com with ESMTPS id 4F2A91 for <bob@example.com>; Fri, 13 Nov 2026 09:14:03 -0500",
        "Received: from [10.0.0.15] (alice-laptop) by mail.example.org with ESMTPSA for <bob@example.com>; Fri, 13 Nov 2026 09:14:02 -0500",
        "From: Alice <alice@example.org>",
        "To: Bob <bob@example.com>",
        "Subject: Lunch?",
    ]

    def test_reading_example(self):
        """Bottom-up: Alice's server first, then Bob's"""
        self.assertEqual(hop_path(self.HEADERS), ["mail.example.org", "mx.example.com"])

    def test_ignores_other_headers(self):
        """Subject lines mentioning 'by' don't count"""
        self.assertEqual(hop_path(["Subject: Sent by me", "Received: from a by b.example.net; now"]), ["b.example.net"])

    def test_case(self):
        """Header names ignore case"""
        self.assertEqual(hop_path(["RECEIVED: from x by Relay.Example.COM; now"]), ["relay.example.com"])

    def test_three_hops(self):
        """A filtering relay in the middle"""
        headers = [
            "Received: from relay.example.com by exchange.corp.example.com; t3",
            "Received: from mail.example.org by relay.example.com; t2",
            "Received: from laptop by mail.example.org; t1",
        ]
        self.assertEqual(hop_path(headers), ["mail.example.org", "relay.example.com", "exchange.corp.example.com"])

    def test_none(self):
        """No Received: headers"""
        self.assertEqual(hop_path(["From: a@b.c"]), [])


if __name__ == "__main__":
    unittest.main()
