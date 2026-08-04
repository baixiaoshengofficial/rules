#!/bin/sh
set -eu

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
rules_file="$repo_dir/HongGuoAD.list"

awk -F, '
  /^[[:space:]]*($|#)/ { next }
  $1 == "DOMAIN" || $1 == "DOMAIN-SUFFIX" {
    if (NF != 2 || $2 !~ /^[[:alnum:]_.-]+$/) {
      printf "invalid domain rule at line %d: %s\n", NR, $0 > "/dev/stderr"
      exit 1
    }
    next
  }
  $1 == "IP-CIDR" {
    if (NF != 3 || $3 != "no-resolve") {
      printf "invalid IP rule at line %d: %s\n", NR, $0 > "/dev/stderr"
      exit 1
    }
    next
  }
  {
    printf "unsupported rule at line %d: %s\n", NR, $0 > "/dev/stderr"
    exit 1
  }
' "$rules_file"

duplicates=$(sed '/^[[:space:]]*#/d; /^[[:space:]]*$/d' "$rules_file" | sort | uniq -d)
if [ -n "$duplicates" ]; then
  printf 'duplicate rules:\n%s\n' "$duplicates" >&2
  exit 1
fi

match_domain() {
  host=$1
  awk -F, -v host="$host" '
    $1 == "DOMAIN" && host == $2 { found = 1 }
    $1 == "DOMAIN-SUFFIX" && (host == $2 || host ~ ("\\." $2 "$")) { found = 1 }
    END { exit found ? 0 : 1 }
  ' "$rules_file"
}

for host in \
  ad.zijieapi.com \
  ads3-normal-lf.zijieapi.com \
  api-access.pangolin-sdk-toutiao.com \
  p1-ad-sign.byteimg.com \
  p9-ad-sign.byteimg.com \
  dig.bdurl.net \
  dig.zjurl.cn
do
  if ! match_domain "$host"; then
    printf 'expected ad host to match: %s\n' "$host" >&2
    exit 1
  fi
done

for host in \
  api.fqnovel.com \
  reading.snssdk.com \
  p3-reading.byteimg.com \
  v3-reading-video.fqnovelvod.com \
  sf3-ttcdn-tos.pstatp.com \
  hongguoduanju.com
do
  if match_domain "$host"; then
    printf 'normal-content host must not match: %s\n' "$host" >&2
    exit 1
  fi
done

grep -Fq 'custom_proxy_group=红果广告`select`[]REJECT' "$repo_dir/baixiaosheng.ini"
if grep -F 'custom_proxy_group=红果广告' "$repo_dir/baixiaosheng.ini" | grep -Fq '[]DIRECT'; then
  printf '红果广告 policy must not allow DIRECT\n' >&2
  exit 1
fi

grep -Fq 'name = "红果广告"' "$repo_dir/baixiaosheng.toml"
grep -Fq 'rule = ["[]REJECT"]' "$repo_dir/baixiaosheng.toml"
grep -Fq 'ruleset = "https://raw.githubusercontent.com/baixiaoshengofficial/rules/main/HongGuoAD.list"' "$repo_dir/baixiaosheng.toml"

printf 'HongGuoAD rules: OK\n'
