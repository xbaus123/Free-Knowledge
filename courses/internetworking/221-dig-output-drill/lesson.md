# Drill: Reading dig

*Chapter 7 · DNS.*

Use this output for every question:

```
$ dig soa marshall.edu
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 1467
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; QUESTION SECTION:
;marshall.edu.                  IN      SOA

;; ANSWER SECTION:
marshall.edu.   3215   IN   SOA   ns1-34.azure-dns.com. dnsadmin.marshall.edu. 2793 3600 1200 259200 3600

;; Query time: 207 msec
;; SERVER: fe80::a416:c0ff:fe30:5464%6#53
```

This quiz mixes multiple choice, true or false, and typed answers (8 questions). Each answer is checked as soon as you give it. Typed answers ignore capitals and extra spaces. A correct answer comes with a short explanation, and a wrong one costs nothing, so try again.
