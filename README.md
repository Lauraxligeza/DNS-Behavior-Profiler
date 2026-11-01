# DNS Behavior Profiler

Ever wondered why different DNS servers sometimes give different answers? Or what actually happens to DNS records and their TTL values when you keep querying them?

I did, so I built this. :)

DNS Behavior Profiler is a Python CLI tool that lets you query multiple DNS resolvers, compare their responses, and monitor how DNS records behave over time.

The idea was pretty simple: instead of just reading about DNS caching and resolution, I wanted to actually see it happening.

## What can it do?

- **Compare DNS resolvers** — Query Google DNS, Cloudflare, Quad9, or any other resolver you specify.
- **Monitor DNS records** — Supports A, AAAA, CNAME, MX, NS, and TXT records.
- **Measure latency** — See how long each resolver takes to respond.
- **Track TTL values** — Watch TTL values change and detect possible cache-related events.
- **Detect record changes** — See when DNS records are added or removed between consecutive successful queries.
- **Keep monitoring** — Run continuous DNS queries at whatever interval you choose.
- **Handle errors** — Timeouts, nonexistent domains, and other common DNS resolution problems.
- **Export results** — Save measurements as CSV or JSONL files for later analysis.

I also added automated tests using pytest, because apparently getting something to work once doesn't necessarily mean it works properly. xD

## Getting started

You'll need Python 3.10+ installed.

Download the project or clone the repository, then open a terminal inside the project folder.

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it (Linux/macOS):

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

And you're ready.

## How to use it

**Query Google DNS:**

```bash
python dns_profiler.py --domain example.com --resolver 8.8.8.8
```

**Compare Google DNS, Cloudflare, and Quad9:**

```bash
python dns_profiler.py --domain example.com --resolver 8.8.8.8 1.1.1.1 9.9.9.9
```

**Want to look at MX records instead?**

```bash
python dns_profiler.py --domain example.com --resolver 1.1.1.1 --type MX
```

**Change how frequently it queries:**

```bash
python dns_profiler.py --domain example.com --resolver 8.8.8.8 --interval 10
```

**Save the results as CSV:**

```bash
python dns_profiler.py --domain example.com --resolver 8.8.8.8 1.1.1.1 --format csv
```

The tool saves results to `dns_results.jsonl` by default, or `dns_results.csv` if you select CSV. You can choose your own filename with `--filename`.

Press `Ctrl+C` when you've had enough DNS for the day.

## What does the output look like?

An example of the terminal output (illustrative values):

```text
[Cycle 1] [8.8.8.8] Records: ['1.2.3.4'] | TTL: 300 | Latency: 25.41 ms
[Cycle 1] [1.1.1.1] Records: ['1.2.3.4'] | TTL: 290 | Latency: 18.20 ms
[Cycle 1] All successfully queried resolvers returned matching records.
```

You can also get alerts when records change, when TTL values increase, or when two resolvers return different records.

## A little about DNS caching

One of the things I was particularly interested in was TTL (Time to Live).

DNS records have TTL values that tell caching resolvers how long they may keep a record before needing to retrieve it again.

By querying the same resolver repeatedly, you can sometimes observe those values decreasing, suddenly increasing, or behaving differently than expected.

An increase might suggest cache-related activity, but it doesn't necessarily prove a cache refresh. Different cache instances and other DNS behavior can also affect what we observe.

And that's exactly what makes it interesting.

## Testing

I've written 14 automated tests with pytest, covering DNS queries, resolver comparisons, timeout handling, record-change detection, TTL analysis, data exports, and input validation.

Run them with:

```bash
python -m pytest -v
```

## Project structure

```text
DNS-Behavior-Profiler/
├── dns_profiler.py
├── requirements.txt
├── README.md
├── .gitignore
└── tests/
    └── test_dns_profiler.py
```

## A few limitations

This is a learning project, not a full-scale DNS monitoring platform.

Resolvers are queried sequentially, monitoring runs until you stop it, and the tool reports observable differences rather than trying to guess exactly why they happened.

Also, DNS responses differing between resolvers isn't automatically a problem. CDNs, load balancing, geographical differences, and caching can all cause perfectly legitimate variations.

## Built with

Python, dnspython, pytest, argparse, CSV, and JSONL.

## Why I built this

I'm learning networking, and I've realized that understanding a protocol on paper and actually watching it behave are two very different things.

My previous project was an ARP Network Mapper, where I explored devices on a local network. This time I wanted to move a little further into DNS and understand what's going on behind the scenes when domain names are resolved.

The best part was probably discovering how many small details there are to think about once you start building something yourself. Error handling, timeouts, comparing responses, deciding what actually counts as a change, making sure the tests pass...

Turns out even a relatively simple idea can teach you quite a lot.
