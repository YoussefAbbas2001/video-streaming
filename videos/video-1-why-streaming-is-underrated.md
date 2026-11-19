# Video 1 — Why Streaming Is Underrated
## ليه الـStreaming أهم بكتير من ما إحنا فاكرين

| | |
|---|---|
| **المدة** | ≈ 5 دقايق (حوالي 650 كلمة كلام) |
| **الـSlides** | 5 · 6 · 16 · 18 · 40 · 44 (من `presentation/MIA_Robotics_Workshop.pptx`) |
| **الـDemos** | Demo 1: الـGlass-to-glass latency بالـclock · الـEgypt cost calculator |
| **قبل التسجيل** | افتح `demos/01_why_streaming/clock.html` على شاشة تانية · جهّز الكاميرا والـreceiver · جرّب `egypt_cost.py` مرة |

> **مفتاح العلامات:** 🎞️ = اعرض الـslide · 🧪 = Demo · 🎥 = لقطة شاشة أو B-roll · ⏱️ = الوقت التقريبي

---

## Opening ⏱️ 0:00

🎞️ **Slide 5** — Video is the primary sensor

أهلاً بيكم، أنا يوسف عباس، وده أول فيديو في سلسلة صغيرة عن الـVideo Streaming في الـROV بتاعنا.

قبل ما نبدأ، تخيلوا معايا حاجة: الـROV نازل تحت الميه 30 متر، والـpilot قاعد فوق قدام الشاشة. الصورة اللي قدامه متأخرة 2 ثانية بس. سؤال بسيط: هل الـROV لسه ممكن نتحكم فيه؟

الإجابة الصادقة: بالعافية. لما الـpilot يشوف الـgripper قرب من الـobject، يكون الـgripper في الحقيقة عدّاه من ثانيتين. فيصحح، والتصحيح نفسه بيوصل متأخر، فيـovershoot تاني. ده مش مشكلة في الـpilot، دي مشكلة في الـsystem.

النهارده حنتكلم عن ليه الـStreaming حاجة underrated جداً عندنا في الفريق، مع إنه بالمعنى الحرفي هو **عين الـpilot**.

## Content Overview

الـcontent اللي حنعرضه:

1. الـVideo هو الـprimary sensor — وليه أي عيب فيه بيضرب المهمة كلها
2. الـStreaming عبارة عن trade-off بين خمس حاجات
3. ليه الـCompression مش رفاهية — والعالم كله ماشي بيه
4. مثال عملي بالجنيه المصري: الفيديو من غير compression يكلف كام؟
5. ليه الـFPS العالي مش معناه latency قليلة
6. الـDemo: نقيس الـglass-to-glass latency بنفسنا

يلّا بينا نبدأ!

---

## 1. Video Is the Primary Sensor ⏱️ 0:40

🎞️ **Slide 5**

الـpilot ما يعرفش أي حاجة عن الـenvironment غير اللي الكاميرات بتوريهوله. عندنا pilot camera، manipulator camera، inspection camera، rear camera، وكل واحدة ليها شغلانة مختلفة واحتياجات مختلفة.

وأي عيب في الفيديو، سواء lag أو freeze أو blur، بيضرب مستوى من مستويات الـsituational awareness: يا إما الـpilot مش شايف، يا إما مش فاهم اللي شايفه، يا إما مش قادر يتوقع حيحصل إيه لما يتحرك.

## 2. Streaming Is a Trade-off ⏱️ 1:10

الـStreaming مش "شغّل الكاميرا وخلاص". هو trade-off بين خمس حاجات بتشد في بعض:

- الـ**Image quality**
- الـ**Latency**
- الـ**Bandwidth**
- الـ**Reliability**
- الـ**Processing resources**

🎥 *(اعرض على الشاشة الجدول ده)*

| | Stream A | Stream B |
|---|---|---|
| Resolution | 1080p | 720p |
| FPS | 60 | 30 |
| Bitrate | 12 Mbps | 2 Mbps |
| Latency | 500 ms | 100 ms |
| Visual quality | High | Moderate |

سؤال ليكم: لو إنتو الـpilot وبتعملوا manipulation task، تختاروا مين؟

مفيش إجابة واحدة صح لكل حاجة، بتفرق حسب المهمة. بس في الـpiloting غالباً الـfeed اللي فيه latency قليلة أهم بكتير من صورة حلوة بس متأخرة. الصورة الحلوة المتأخرة بتكدب على الـpilot.

## 3. The World Runs on Compression ⏱️ 1:50

🎞️ **Slide 6** — The world quietly runs on video compression

حاجة ناس كتير ما تعرفهاش: حوالي **65%** من الـtraffic بتاع الإنترنت كله في العالم فيديو. ده حسب تقرير Sandvine عن سنة 2022.

وكل جيل من الـcodecs بيحتاج تقريباً **نص الـbits** للجيل اللي قبله بنفس الجودة: H.264 سنة 2003، وبعده HEVC سنة 2013، وبعده VVC سنة 2020.

والفريق اللي عمل H.264 خد **Emmy** مرتين، 2008 و2009. Emmy لمهندسين مش لممثلين! لدرجة إن واحد من الـITU وصف الـstandard ده إنه "a jewel in the crown of international standards collaboration".

يعني Netflix والـvideo calls والكاميرات والدرونز، والـ8 كاميرات بتوعنا كمان، كلهم موجودين لأن في حد صغّر الـbits. ومحدش بياخد باله من ده غير لما يبوظ.

## 4. A Practical Example in Egyptian Pounds ⏱️ 2:30

🎞️ **Slide 16** — Raw bandwidth = pixels × bits × frames

خلونا نحسبها. كاميرا 1080p، يعني 1920 × 1080، بـ30 frame في الثانية، و24 bit لكل pixel:

1920 × 1080 × 30 × 24 ≈ **1.49 Gigabit في الثانية**.

🎞️ **Slide 18** — One hour of video on an Egyptian home internet line

طب ده يعني إيه بالجنيه؟ باقة WE الأساسية للإنترنت المنزلي 100 GB بـ150 جنيه قبل الضريبة، يعني حوالي **1.71 جنيه للـGB**.

- ساعة فيديو raw = حوالي **672 GB** = حوالي **1150 جنيه** في الساعة. والباقة كلها، الـ100 GB، بتخلص في **9 دقايق**!
- نفس الساعة بـH.264 على 5 Mbps = حوالي 2.25 GB = حوالي **4 جنيه**.

يعني الـcompression خلّى الفيديو أرخص حوالي **300 مرة**. ولو عندك خط 30 Mbps، الفيديو الـraw محتاج سرعة أكبر من خطك بحوالي 50 مرة، يعني مستحيل يتبعت live أصلاً.

🧪 **Demo (30 ثانية):** شغّل في الـterminal:

```bash
python3 demos/01_why_streaming/egypt_cost.py --cameras 8 --width 1280 --height 720 --minutes 15
```

وقول: "ده نفس الحساب بس لـ8 كاميرات 720p لمدة ربع ساعة، يعني مهمة MATE تقريباً. شوفوا الـraw محتاج كام ضعف من الـline speed."

> ملاحظة: الأسعار بتتغير كتير، اتأكد منها على te.eg قبل التسجيل.

## 5. High FPS ≠ Low Latency ⏱️ 3:30

غلطة منتشرة جداً: "خلّي الـFPS 60 والصورة تبقى أسرع". لأ.

الـFPS بيقول إنت بتبعت كام صورة في الثانية، لكن الـlatency بتقول كل صورة بتوصل **متأخرة قد إيه**. ممكن يبقى عندك 60 FPS والصورة متأخرة نص ثانية، لأن الـencoder ماسك frames في الـbuffer، أو الـplayer عامل cache ثانية كاملة.

🎞️ **Slide 40** — Latency is designed, not discovered

في الـnotebook بتاعنا قسنا ده: الـx264 بالـdefault settings مسك **41 frame** قبل ما يطلع أول frame، يعني حوالي 1.4 ثانية. وبـ`-tune zerolatency` مسك **صفر**. نفس الكمبيوتر ونفس الكاميرا، والفرق في setting واحد بس.

## 6. Demo 1 — Glass-to-Glass Latency ⏱️ 4:00

🎞️ **Slide 44** — Your measurement toolbox (الـglass-to-glass في آخر سطر)

🧪 **Demo (45 ثانية):**
1. افتح `demos/01_why_streaming/clock.html` full screen، ساعة بالـmilliseconds.
2. وجّه كاميرا الـROV على الشاشة دي.
3. اعرض الفيديو اللي واصل جنب الساعة.
4. صوّر الاتنين بالموبايل في صورة واحدة.

الـ**glass-to-glass latency** = الوقت على الساعة الحقيقية − الوقت اللي ظاهر جوه الفيديو. يعني من "الزجاج" بتاع عدسة الكاميرا لحد "الزجاج" بتاع شاشة الـpilot.

خد 10 صور مش صورة واحدة، واحسب الـ**median** والـ**worst case**، لأن الـpilot بيعاني من أسوأ لحظة مش من المتوسط.

## Takeaway ⏱️ 4:40

الخلاصة:

> جودة الفيديو مش بس عدد الـpixels. هي **قد إيه المعلومة المفيدة بتوصل للـpilot بسرعة**.

في الفيديو الجاي حنمشي ورا الـframe من الكاميرا لحد الشاشة، ونشوف بالظبط فين الوقت والأداء بيضيعوا.

شكراً ليكم، ونتقابل في الفيديو الجاي!
