# ISL P1 繁體中文快速入門

這是一套可以離線執行的基本光譜數值語言。它不是 AI 語義自動理解模型。

## 一分鐘測試

```powershell
python -m spectral_public.cli check examples/hello.isl
python -m spectral_public.cli run examples/hello.isl
python -m unittest discover -s tests -v
```

語法包含 `axis`（宣告軸）、`record`（建立帶來源資訊的紀錄）、`let`（運算結果命名）、`print`（列印結果）。

`record` 的 `text` 是原始自然語言敘述，`context` 是使用情境，`provenance` 用來解釋數值從何而來。初版例子採用**人工指定的合成數值**，不會從文字自行計算「真實的快樂程度」。

可以使用的五種數值運算是 `intersect`（區間交集）、`union`（不偷補中間空隙的聯集）、`blend`（加權插值）、`cosine`（候選相似度）和 `filter`（確定性數值篩選）。

若遇到非法區間、不同軸直接混算、缺少來源、未宣告軸、未知識別字，程式會拒絕執行並指出位置。

## 對外版定位

ISL 是獨立、漸進開發的語言，早期只解決有限維度的可計算光譜問題。後續可研究資料驅動編碼器、檢索與生成，但不能把尚未完成的能力說成已經實作。

目前 GitHub 可公開閱讀；是否提供再利用授權，仍由作者另外決定。
