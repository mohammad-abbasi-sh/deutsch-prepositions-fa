# deutsch-prepositions-fa — حرف‌های اضافهٔ آلمانی برای فارسی‌زبان‌ها

یک **Agent Skill** قطعی برای بخشی از دستور زبان آلمانی که فارسی‌زبان‌ها
هر روز در آن گیر می‌کنند: حرف‌های اضافه. بعد از
[`deutsch-fa`](https://github.com/mohammad-abbasi-sh/deutsch-fa)
(آرتیکل + ۴ حالت)،
[`deutsch-verbs-fa`](https://github.com/mohammad-abbasi-sh/deutsch-verbs-fa)
(صرف فعل) و
[`deutsch-word-order-fa`](https://github.com/mohammad-abbasi-sh/deutsch-word-order-fa)
(ترتیب کلمات)، این ستون چهارم است — *warten auf* در برابر *warten für*،
*nach Berlin* در برابر *zu Berlin*، *am Montag* در برابر *in Montag*، و
نه حرف اضافهٔ دوحالتی که با Wo/Wohin حالتشان عوض می‌شود.

فارسی برای «در» و «به» یک کلمه دارد؛ آلمانی یک دستگاه کامل: هر حرف اضافه
یک حالت می‌خواهد، نه‌تایشان با Wo/Wohin عوض می‌شوند، هر فعل حرف اضافهٔ
خودش را می‌خواهد و زمان با `am`/`im`/`um` قاعدهٔ ثابت دارد.
`deutsch-prepositions-fa` همهٔ این انتخاب‌ها را **قطعی** می‌کند: یک موتور
پایتون بدون وابستگی + جدول دستی A1 تا B1 (۳۸ حرف اضافه، ۹۲ ترکیب
فعل+حرف اضافه با معنی فارسی)، با همهٔ توضیح‌ها به فارسی.

بدون فراخوانی مدل. بدون دانلود. بدون کلید API. فقط کتابخانهٔ استاندارد
پایتون ۳٫۸ به بالا.

## مسئله

```
زبان‌آموز می‌نویسد:  Ich warte für dich.   /  Ich fahre zu Berlin.
ایجنت (از حفظ):      درست به نظر می‌رسد ✓   ← هر دو غلط‌اند و حالا
                                              زبان‌آموز هر دو را حفظ می‌کند

با deutsch-prepositions-fa:
$ python3 scripts/prepositions.py check "Ich warte für dich."
✗ [DPR-01] «warten» با «auf» + Akk می‌آید، نه «für».
  درستش: Ich warte auf dich.
```

## چه چیزی داخلش است

```
skills/deutsch-prepositions-fa/
  SKILL.md                     اسکیل ایجنت (قرارداد)
  scripts/prepositions.py      موتور — lookup, prep, wechsel, check, fix, quiz, anki
  data/prepositions.json       ۳۸ حرف اضافه + ۹۲ ترکیب فعل+حرف اضافه (دستی بررسی‌شده)
  references/
    preposition-tables.md      جدول چهار گروه حالتی، Wechsel، ادغام‌ها، ترکیب‌های da-/wo-
    persian-traps.md           تله‌های تداخل فارسی (nach/zu، seit/vor، auf/über)
cursor/deutsch-prepositions-fa.mdc  قانون کرسر (همان قرارداد، خلاصه‌شده)
mcp-server/                    سرور MCP (stdio) با ۷ ابزار
tests/                         ۸۹ تست، همه پاس (unittest استاندارد)
dist/deutsch-prepositions-fa-skill.zip  بستهٔ آماده برای آپلود در Claude.ai
```

دستورها:

```bash
python3 scripts/prepositions.py lookup warten
python3 scripts/prepositions.py lookup "sich freuen"   # auf / über / für — سه معنی
python3 scripts/prepositions.py prep auf
python3 scripts/prepositions.py wechsel in wohin        # → Akkusativ
python3 scripts/prepositions.py check "Ich warte für dich."
python3 scripts/prepositions.py fix "Ich stelle das Buch auf dem Tisch."
python3 scripts/prepositions.py quiz --n 5 --level A1 --seed 42
python3 scripts/prepositions.py anki --kind verbs --out cards.tsv   # ۹۲ کارت
```

## نصب

**Claude Code** — پوشهٔ `skills/deutsch-prepositions-fa/` را در پوشهٔ
اسکیل‌های پروژه (یا `~/.claude/skills/` برای استفادهٔ سراسری) کپی کنید.

**Claude.ai** — فایل `dist/deutsch-prepositions-fa-skill.zip` را به‌عنوان
اسکیل آپلود کنید.

**Cursor** — فایل `cursor/deutsch-prepositions-fa.mdc` را در
`.cursor/rules/` و پوشهٔ `skills/deutsch-prepositions-fa/` را در پروژه
کپی کنید. Windsurf / Cline / Continue: ببینید `cursor/README.md`.

**هر کلاینت MCP** — سرور stdio را معرفی کنید:

```json
{
  "mcpServers": {
    "deutsch-prepositions-fa": {
      "command": "python3",
      "args": ["/path/to/mcp-server/deutsch_prepositions_mcp_server.py"]
    }
  }
}
```

ابزارها: `lookup_verb`، `preposition`، `wechsel`، `check_sentence`،
`quiz`، `anki_export`، `list_prepositions`.

## محدودیت‌های صادقانه

- فهرست، واژگان اصلی A1 تا B1 است (نسخهٔ ۱٫۰٫۰) — جایگزین دیکشنری برای
  فعل‌های خارج از فهرست نیست؛ فعل ناشناخته «در فهرست نیست» می‌گیرد، نه
  جواب حدسی.
- بررسی‌کنندهٔ جمله عمداً محافظه‌کار است: فقط جمله‌های سادهٔ زمان حال.
  عبارت مکانی (`Ich warte in dem Bus`)، عبارت زمانی (`am Montag`) و فعل
  مبهم (`hängen`، هم مکان هم حرکت) را حدس نمی‌زند و رها می‌کند.
  «مشکلی پیدا نشد» یعنی «درست است» نیست.
- تفاوت `sich freuen auf` (آینده) و `über` (حال) به بافت زمانی نیاز دارد
  که بررسی‌کننده ندارد — هر دو پذیرفته می‌شوند؛ تفاوت در
  `references/persian-traps.md` آمده است.
- مرجع قطعی است، نه معلم: دربارهٔ سبک و طبیعی بودن جمله قضاوت نمی‌کند.

## مجوز

MIT — ببینید LICENSE.
