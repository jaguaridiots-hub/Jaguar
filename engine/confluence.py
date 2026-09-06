from engine.score import score
from market.scanner import confidence

print("====== Jaguar AI Confluence ======")

ai_score = score
mtf_score = confidence

final_score = ai_score + mtf_score

print(f"AI Score            : {ai_score}")
print(f"MTF Confidence      : {mtf_score}%")
print(f"Combined Score      : {final_score}")

print()

if final_score >= 80:
    signal = "🔥 STRONG BUY"

elif final_score >= 65:
    signal = "🟢 BUY"

elif final_score >= 45:
    signal = "🟡 WAIT"

else:
    signal = "🔴 SELL"

print("Final Decision :", signal)
