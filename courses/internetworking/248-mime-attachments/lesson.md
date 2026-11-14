# Attachments and MIME

*Chapter 8 · Mail.*

SMTP was built for short lines of plain **7-bit ASCII** text. No pictures, no accents, no PDFs. **MIME** (Multipurpose Internet Mail Extensions) is how mail carries all of those without changing SMTP itself.

## Labels: Content-Type

MIME adds headers that say what the content is:

```
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
```

The **type/subtype** names are the same media types the web uses: `text/plain`, `text/html`, `image/png`, `application/pdf`.

## Parts: multipart

A message with an attachment is **`multipart/mixed`**. Its body is split into parts by a **boundary** string that appears nowhere else:

```
Content-Type: multipart/mixed; boundary="XyZ42"

--XyZ42
Content-Type: text/plain; charset=utf-8

Here's the report.
--XyZ42
Content-Type: application/pdf; name="report.pdf"
Content-Disposition: attachment; filename="report.pdf"
Content-Transfer-Encoding: base64

JVBERi0xLjcKJcfsj6IKNSAwIG9iago8PC9MZW5ndGggNiAwIFIvRmlsdGVyIC9GbGF0ZUR
...
--XyZ42--
```

The final boundary has two extra dashes on the end. Other common kinds: **`multipart/alternative`** (the same message as plain text *and* HTML, and the client shows the best one) and **`multipart/related`** (HTML with its images inline).

## Encoding: base64

A PDF is binary, and SMTP wants text. **`Content-Transfer-Encoding: base64`** turns every 3 bytes into 4 printable characters, so attachments grow by about **a third** (4/3) on the wire. A 15 MB file takes about 20 MB as base64, which is why mail size limits feel stricter than the file sizes you attach. `quoted-printable` is the other encoding, for text that's mostly ASCII with a few accented characters.

## Why attachments are risky

An attachment can be anything. The `Content-Type` and the file name are just **labels the sender chose**: `invoice.pdf` can really be a program. Office documents can carry **macros**, and archives can hide executables. That's why mail servers scan attachments, block risky types (`.exe`, `.js`, `.iso`), and sometimes open them in a sandbox first, as you'll see later in this chapter.

Next, a check on MIME.
