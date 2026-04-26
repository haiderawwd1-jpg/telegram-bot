        sent = 0  
        cap = m.caption if m.caption else ""  

        for u in users:  
            try:  
                bot.send_photo(  
                    u[0],  
                    m.photo[-1].file_id,  
                    caption=cap  
                )  
                sent += 1  
            except:  
                pass  

        steps.pop(uid, None)  
        bot.send_message(uid, f"تم إرسال الصورة إلى {sent}")

================= RUN =================

while True:
try:
bot.infinity_polling(skip_pending=True)
except:
time.sleep(5)
