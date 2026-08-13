# ผลเอาไปลองกับโปรเจกต์จริง

**6 โปรเจกต์ + 1 รอบเขียนลง Figma จริง · 13 สิงหาคม 2026 · ระดับ T1 (token) ทั้งหมด**

เอกสารนี้คือที่มาของคำว่า "ทดสอบแล้ว" ทุกจุดใน README · ทุกตัวเลขวัดจริง
โปรเจกต์เป็นของภายในบริษัท จึงเขียนแค่ **โปรไฟล์ของ stack** ไม่ระบุชื่อ

> **ระวังอย่าอ่านเกินกว่าที่มันบอก** — 6 รอบแรกทดสอบ *การอ่านโค้ดออกมาเป็น token*
> · รอบที่ 7 ทดสอบ *การเขียน token ลง Figma จริงแล้วอ่านกลับมาเทียบ*
> · ระดับ component / หน้าจอ / flow **ยังไม่เคยรันกับโปรเจกต์จริงเลยสักตัว**

---

## สรุป

| # | Stack | Token | เทียบได้ | เจอปัญหา |
|---|---|---|---|---|
| 1 | React Router 8 + Tailwind v4 + shadcn | 488 | 100% | 4 |
| 2 | Next 15 + Tailwind v3 (config ซ้อน 437 บรรทัด) | 243 | 96% | 2 |
| 3 | Vite 7 + TanStack Router + TW v4 + bun | 75 | 97% | 3 |
| 4 | เหมือน #3 + มี Playwright e2e อยู่แล้ว | 193 | 93% | 5 |
| 5 | Flutter (ไม่ใช่โปรเจกต์ต้นแบบ) + GetX | 52 | 100% | 3 |
| 6 | Flutter + token 3 ชั้น + go_router/GetX | 142 | 100% | 3 |

**รวม 22 ปัญหา** · selftest จาก 38 → 61 ข้อ · ทุกข้อที่เจอถูกล็อกด้วย assertion
เพื่อไม่ให้ย้อนกลับมา

---

## รอบที่ 1 — React Router 8 + Tailwind v4

- **`oklch()` อ่านไม่ออก** — Tailwind v4 กับ shadcn เขียนสีเป็น oklch แทบทั้งหมด
  31 token อ่านไม่ออกและจะถูกรายงานว่า **mismatch** ทั้งที่ Figma ถูก
  → แปลงตาม CSS Color 4 (OKLCH → OKLab → LMS → linear sRGB)
- **Tailwind v4 ไม่มีไฟล์ config** — theme ย้ายเข้า CSS (`@theme`) · discovery สั่งให้ไปหา
  `tailwind.config.*` แล้วหาไม่เจอ → สรุปผิดว่า "ไม่มี Tailwind theme"
- **คำเตือน "declared twice" วินิจฉัยผิด** — บอกว่าน่าจะเป็น nested object แต่สาเหตุจริงคือ
  light/dark อยู่ไฟล์เดียวใช้ชื่อเดียวกัน
- **React Router 7+ framework mode** = Remix เดิม · route อยู่ใน `app/routes.ts`

**ตัวเลขที่ได้เรียนรู้:** 531 custom property แต่ใช้เป็นค่าได้ตรง ๆ แค่ **43%** ที่เหลือเป็น
`var()` alias 260 · oklch 31 · calc 6 → หลังทำ resolver เสร็จกลับมาวัดใหม่ได้ **100%**

## รอบที่ 2 — Next 15 + Tailwind v3

- **ไม่มี parser สำหรับ nested object** — regex เก็บแค่ leaf key ทำให้ `brand.500` กับ
  `accent.500` ชนกันแล้วทิ้งตัวหลังเงียบ ๆ → เพิ่ม `format: "json-tree"` ที่ต่อ key path
  (ผลจริง: 41 สี · 150 typography · 10 shadow ไม่ชนเลย · `fontSize` ที่เป็น array
  ออกมาครบทั้งขนาดและ line-height)
- **alias ยัง resolve ไม่ได้** → เพิ่ม `--resolve-aliases`

**บั๊กในโค้ดที่เพิ่งเขียนชั่วโมงนั้น:** resolver รอบแรกได้ "resolved 11, unresolved 30"
ทั้งที่ค่าอยู่ในไฟล์ที่ใส่ไว้แล้ว · สาเหตุ: `colors/primary/DEFAULT` พอ normalize เป็น key
กลายเป็น `primary-default` **ซึ่งชนกับ custom property ที่มันชี้ไป** → จองคีย์ตัวเอง →
resolve มาเจอตัวเอง → ถูกข้าม · **alias ทุกตัวค้าง แต่รายงานดูปกติ**
แก้โดย index ค่าจริงก่อน ค่อย index reference

## รอบที่ 3 — Vite + TanStack Router

- **alias ที่ฝังในนิพจน์ไม่เคยถูกแทนค่า** — `calc(var(--radius) - 4px)` (convention ของ
  shadcn, เจอ 2 ใน 3 โปรเจกต์เว็บ) · resolver แทนค่าเฉพาะตอนทั้งค่าเป็น reference
  → radius ค้างเป็น string → **Figma เก็บ string เป็น corner radius ไม่ได้ = push ไม่ได้เลย**
- **`calc()` ไม่เคยคำนวณ** → เพิ่มการคำนวณแบบแคบ ๆ `calc(0.625rem - 4px)` → **6px**
- **`bun.lock` vs `bun.lockb`** — bun เปลี่ยนเป็น lockfile แบบ text แล้ว · discovery
  เขียนไว้แค่ชื่อเก่า → โปรเจกต์ bun ปัจจุบันถูกอ่านเป็น npm
- **TanStack Router ไม่มีในตาราง flow** → มัน generate `routeTree.gen.ts` ซึ่ง
  trace ง่ายที่สุดในบรรดา router ทั้งหมด

**ของที่ทำงานถูก:** โปรเจกต์นี้ไม่มี `.dark` block ผมใส่ config ผิด — `between` guard
**hard error พร้อมบอกวิธีแก้** แทนที่จะเงียบ ๆ อ่านทั้งไฟล์แล้วปนโหมดกัน

## รอบที่ 4 — stack เดียวกับรอบ 3 แต่เจอมากที่สุด

ผมทายว่าจะเจอน้อยลงเพราะ stack ซ้ำ · **เจอ 5 ข้อ มากที่สุดในทุกรอบ** เพราะสิ่งที่เจอ
ไม่ได้มาจาก stack แต่มาจาก**สิ่งที่ทีมทำต่างกัน** — โปรเจกต์นี้มีคนเขียน Playwright
e2e visual test ไว้แล้ว

- **skill เขียนผิด** — `evidence-without-storybook.md` บอกว่า "จับภาพจากแอปจริง
  บังคับสถานะ error/empty ไม่ได้" · **บนเว็บมันผิด** เพราะ Playwright intercept
  request ได้ (`route.fulfill({status: 404})`) · ประโยคนั้นมาจากประสบการณ์ mobile
  แล้วเหมารวมโดยไม่มีหลักฐาน → แก้ให้บอกว่าบนเว็บ no-catalog ใกล้เคียง catalog
  มากกว่าที่หน้านั้นบอกไว้
- **discovery ไม่มองหาฐานเทียบที่มีอยู่แล้ว** — โปรเจกต์มี `visual-smoke.spec.ts`
  ถ่าย 6 route × 2 viewport พร้อม stub API → เพิ่มว่าให้ grep `page.screenshot`
  ก่อนสรุปว่าไม่มีฐานเทียบ
- **แต่มันใช้เทียบ Figma ไม่ได้ เพราะ `fullPage: true`** — ความสูงเปลี่ยนตามข้อมูล
  ไม่มีทางตรงกับเฟรมขนาดคงที่ · ถูกสำหรับ regression triage ผิดสำหรับเทียบดีไซน์
- **lockfile 2 ตัว** (`bun.lock` + `package-lock.json`) — กฎ D2 ไม่ครอบ
- **คำเตือน "declared twice" ต้องมีสาเหตุที่ 3** — ชื่อถูกนิยามใน `:root` แล้วเชื่อมใน
  `@theme inline` = โครง 2 ชั้นของ Tailwind v4

## รอบที่ 5 — Flutter ตัวแรกที่ไม่ใช่โปรเจกต์ต้นแบบ

**รอบที่เจอข้อร้ายแรงที่สุดในทั้ง 6 รอบ**

- `dart-color` match แค่รูปแบบ named-argument ใน ThemeExtension constructor ·
  โปรเจกต์นี้เขียน `static const bgColor = Color(0xffF0F5F9);` → **ดึงได้ 0 จาก 52 สี**
- **และสิ่งที่ตามมาแย่กว่านั้น** — มันรายงานว่า `Families with no tokens found: color`
  ซึ่งตามกฎของ skill เอง "family ที่ไม่มี = finding ต้องจดไว้" · **pattern ที่พังกำลังถูกฟอก
  เป็นข้อสรุปที่มั่นใจว่า "โปรเจกต์นี้ไม่มี colour token"** ทั้งที่มี 52 ตัว —
  ใช้กลไกความซื่อสัตย์ที่ออกแบบไว้เอง มาโกหก
  → ไฟล์ที่ glob เจอแต่ดึงไม่ได้อะไรเลย = **hard error** · จับ config ผิดของผมเองได้ในรันถัดไปทันที
- **Flutter page มีแต่ `go_router`** — โปรเจกต์นี้ใช้ GetX ซึ่งให้ทั้ง routing + DI + state

**ผลอ่านโปรเจกต์นี้หลังเครื่องมือถูก:** 52 สี · typography **PARTIAL** (family กับ 9 น้ำหนัก
เป็น token แต่ text style เป็นฟังก์ชันที่รับ fontSize เข้ามา → ไม่มี size scale) ·
shadow **ABSENT** (`BoxShadow` inline 94 ไฟล์)

## รอบที่ 6 — Flutter, token 3 ชั้น

| ชั้น | รูปแบบ |
|---|---|
| primitive | `class AppPalette { static const neutralLevel00 = Color(0xFF0D0D0D); }` |
| theme-blind | `static const white = AppPalette.white;` |
| semantic | `factory AppColorsTheme.light() => AppColorsTheme(textDefault: AppPalette.neutralLevel00, …)` |

- **alias ไม่ได้มีแต่ใน CSS** — `AppPalette.neutralLevel00` คือ alias แบบเดียวกับ
  `var(--x)` เป๊ะ ๆ แค่เขียนเป็น Dart identifier · ในไฟล์เดียวมี **226 ตัว** ·
  resolver รู้จักแค่ CSS กับ DTCG → ชั้น semantic ทั้งชั้น resolve ไม่ได้
  → dotted identifier นับเป็น reference แล้ว + preset `dart-ref`
- **`flutter.md` สมมติว่าทุกโปรเจกต์เป็น ThemeExtension ชั้นเดียว** — ความแคบแบบเดียว
  กับที่รอบ 5 เจอใน `dart-color`
- **router 2 ตัวใน pubspec เดียว** (`get` + `go_router`)

**ผล:** 142 token · เทียบได้ 100% · 110 ตัวใน semantic layer resolve ผ่าน alias

---

## รอบที่ 7 — เขียนลง Figma จริงเป็นครั้งแรก

6 รอบแรกทดสอบแค่**ฝั่งอ่านโค้ด** · การเทียบใช้ dump จำลองที่สร้างจาก token ที่ดึงมาเอง
ซึ่งพิสูจน์ได้แค่ว่าสคริปต์สอดคล้องกับตัวเอง **ไม่ได้พิสูจน์ว่า Figma รับค่าไปแล้วคืนค่าเดิม**

รอบนี้สร้างไฟล์ Figma เปล่าใน draft ส่วนตัว (ไม่ใช่ไฟล์งาน) แล้วรันวงจรเต็ม:

```
โค้ด → ดึง → resolve alias → คำนวณ calc → push เข้า Figma
     → dump กลับด้วย getLocalVariablesAsync → token_diff
```

**ผล: 39/39 value-exact · exit 0** (34 สี + 5 radius จากโปรเจกต์รอบที่ 3)

### เจอ 2 อย่าง

**1 · config ที่จับ 2 ชั้นพร้อมกัน จะสร้าง variable ซ้ำทุกตัว**

config ของรอบที่ 3 มี 2 source อยู่ใน family เดียวกัน — ชั้นนิยาม (`:root`) กับชั้น bridge
(`@theme inline`) · token ตัวเดียวกันจึงถูกดึงมา 2 ครั้ง (`accent` และ `color-accent`)
→ ถ้า push ไปตรง ๆ จะได้ **variable ซ้ำ 34 ตัวจาก 68** ตัวที่สองชื่อ `color/color/accent`

**จับได้เพราะอ่าน payload ก่อนเขียน** ไม่ใช่เพราะเครื่องมือเตือน · เขียนลง `web.md` แล้วว่า
อย่าชี้ family เดียวไปที่ 2 ชั้น — ดึงชั้นนิยาม แล้วค่อยทำ bridge เป็น alias ทีหลัง

**2 · Figma เก็บสีเป็น float แล้วคืนค่ามาเพี้ยน**

ส่ง `0.956863` ไป ได้กลับมาเป็น `0.9568629860877991` · วงจรรอดได้เพราะ `norm_color`
ปัดเป็น 0–255 ก่อนเทียบ — ซึ่งเดิม**เป็นการเดา ตอนนี้วัดแล้ว** และล็อกด้วย assertion
ที่ใช้ค่าจริงจาก Figma ไม่ใช่ค่าที่แต่งขึ้น

### ที่ยังไม่ได้ทดสอบในรอบนี้

text style · effect style · component · การ bind variable เข้ากับ node ·
โหมด light/dark 2 mode ในคอลเลกชันเดียว · ไฟล์ที่มี variable อยู่ก่อนแล้ว (`ignoreFigma`)

---

## บทเรียนที่ใหญ่กว่าตัวบั๊ก

**1 · "พิสูจน์แล้ว" แปลว่าพิสูจน์กับ *หนึ่งโปรเจกต์* ไม่ใช่กับ *stack นั้น***

รอบ 5 กับ 6 เจอความแคบแบบเดียวกันคนละที่ — `dart-color` แคบเพราะเขียนจากโปรเจกต์ต้นแบบ
`flutter.md` แคบเพราะเขียนจากโปรเจกต์ต้นแบบ · Flutter ตัวที่สองเจอบั๊กที่ Flutter ตัวแรก
ไม่มีทางเจอ เพราะตัวแรกคือที่มาของ pattern

**2 · การอ่านหาความขัดแย้งได้ · การรันหาสิ่งที่ขาดหายได้**

ก่อนหน้านี้ทำ adversarial audit 3 reviewer เจอ 24 ข้อ — **ไม่มีข้อไหนเป็น oklch,
Tailwind v4, หรือ nested parser เลย** เพราะทุก reviewer อ่านไฟล์ชุดเดียวกับที่ผมเขียน ·
บ่ายเดียวกับโปรเจกต์จริงเจอครบทั้งสาม

**3 · จำนวนที่เจอไม่ลดลงตามรอบ**

4 → 2 → 3 → 5 → 3 → 3 · รอบที่ stack ซ้ำที่สุด (รอบ 4) กลับเจอมากที่สุด
เพราะตัวแปรจริงคือ **ทีมทำอะไรต่างกัน** ไม่ใช่ framework

---

## ยังไม่ได้ทดสอบ

- **ระดับ T2 / T3 / T4** — component, หน้าจอ, flow · ยังไม่เคยรันกับโปรเจกต์จริง
- **Vue / Nuxt / Svelte / Angular / SwiftUI / Compose** — ยังไม่เคยแตะ
- ตัวอ่าน xcassets และตัว generate เส้น flow — ยังไม่มี เอกสารบอกไว้ว่าต้องเขียนเอง
