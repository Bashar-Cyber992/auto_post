import os
import urllib.parse
import requests
from google import genai
from google.genai import types

# ================= ================= =================
# 1. إعداد المفاتيح والبيانات (Configuration)
# ================= ================= =================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PAGE_ACCESS_TOKEN = os.environ.get("FACEBOOK_API_KEY")



client = genai.Client(api_key=GEMINI_API_KEY)

# ================= ================= =================
# 2. دالة توليد نص البوست + وصف الصورة (Gemini 3.6 Flash)
# ================= ================= =================
def generate_cyberdose_content(topic: str) -> dict:
    print("[+] Generating post text & image prompt with Gemini...")
    
    system_prompt = (
        "أنت كاتب محتوى ومدير شبكات اجتماعية لصفحة 'جرعة سيبرانية | CyberDose'.\n\n"
        "المطلوب استخراج مخرجات بأسلوب محدد عبر فاصل صريح [SPLIT] بين نص البوست ووصف الصورة:\n\n"
        "أولاً: نص المنشور (باللغة العربية):\n"
        "- بدون استخدام أي نجوم (**) أو رموز Markdown.\n"
        "- مريح للعين، متباعد الأسطر، ومزود بإيموجيات حيوية.\n"
        "- يحتوي على مقدمة، صلب موضوع بنقاط (أرقام أو إيموجيات)، وخاتمة تفاعلية مع هاشتاغات.\n\n"
        "ثانياً: اترك السطر الفاصل التالي تماماً كما هو: [SPLIT]\n\n"
        "ثالثاً: وصف الصورة (باللغة الإنجليزية حصراً):\n"
        "- اكتب وصفاً بصرياً دقيقاً باللغة الإنجليزية (English Image Prompt) يصلح لنماذج الصور.\n"
        "- يعكس موضوع البوست بأسلوب سيبراني مستقبلي (Futuristic, Cyberpunk, Glowing UI, Dark Blue/Neon tones, 8k resolution).\n"
        "- اقتصر في الرد على المخرجات المطلوبة فقط دون أي مقدمات أو ملاحظات جانبية."
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=f"صغ محتوى ووصف صورة لموضوع: {topic}",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
            )
        )
        
        raw_text = response.text.strip()
        
        if "[SPLIT]" in raw_text:
            post_text, image_prompt = raw_text.split("[SPLIT]", 1)
            return {
                "post_text": post_text.strip(),
                "image_prompt": image_prompt.strip()
            }
        else:
            return {
                "post_text": raw_text,
                "image_prompt": f"A futuristic cybersecurity 3D render about {topic}, neon blue lights, highly detailed, 8k"
            }

    except Exception as e:
        print(f"[-] Error generating content from Gemini: {e}")
        return {"post_text": "", "image_prompt": ""}

# ================= ================= =================
# 3. دالة توليد الصورة المجانية بمقاس فيسبوك (Pollinations API)
# ================= ================= =================
def generate_image_free(prompt: str, output_filename: str = "post_image.jpg") -> str:
    print("[+] Generating free image with Pollinations (1200x675 Facebook Format)...")
    try:
        # ترميز النص ليكون مناسباً لروابط URL
        encoded_prompt = urllib.parse.quote(prompt)
        
        # أبعاد فيسبوك الأفقية المثالية 1200x675
        width = 1200
        height = 675
        
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
        
        response = requests.get(url, timeout=45)
        
        if response.status_code == 200:
            with open(output_filename, "wb") as f:
                f.write(response.content)
            print(f"[+] Image generated and saved successfully as '{output_filename}'")
            return output_filename
        else:
            print(f"[-] Image generation failed with status code: {response.status_code}")
            return ""
            
    except Exception as e:
        print(f"[-] Error generating free image: {e}")
        return ""

# ================= ================= =================
# 4. دالة نشر الصورة مع الكابشن على الفيسبوك (Facebook API)
# ================= ================= =================
def post_photo_to_facebook(image_path: str, caption_text: str) -> bool:
    print("[+] Publishing Photo & Caption to Facebook...")
    url = "https://graph.facebook.com/v26.0/me/photos"
    
    payload = {
        'caption': caption_text,
        'access_token': PAGE_ACCESS_TOKEN
    }
    
    try:
        with open(image_path, 'rb') as img_file:
            files = {'source': img_file}
            response = requests.post(url, data=payload, files=files, timeout=30)
            result = response.json()
            
        if "id" in result:
            print(f"[+] Post published successfully! Photo ID: {result['id']}")
            return True
        else:
            print(f"[-] Facebook API Error: {result}")
            return False
    except Exception as e:
        print(f"[-] Connection/File Error: {e}")
        return False

# ================= ================= =================
# 5. خط السير الكامل (Complete Automated Pipeline)
# ================= ================= =================
if __name__ == "__main__":
    # الموضوع المطلوب
    post_topic = "موضوع عشوائي يختص بالأمن السيبراني وبما يعكس محتوى الصحفة جرعة سيبرانية"
    
    # الخطوة 1: توليد النص والوصف عبر Gemini
    content_data = generate_cyberdose_content(post_topic)
    
    if content_data["post_text"] and content_data["image_prompt"]:
        print("\n--- المعاينة البرمجية ---")
        print("📝 النص:\n", content_data["post_text"][:150], "...")
        print("🖼️ الوصف:\n", content_data["image_prompt"])
        print("---------------------------\n")
        
        # الخطوة 2: توليد الصورة المجانية بحجم 1200x675
        saved_image_path = generate_image_free(content_data["image_prompt"])
        
        # الخطوة 3: النشر المباشر على الفيسبوك إذا نجح إنشاء الصورة
        if saved_image_path and os.path.exists(saved_image_path):
            post_photo_to_facebook(saved_image_path, content_data["post_text"])
        else:
            print("[-] Image generation failed, skipping Facebook post.")
    else:
        print("[-] Content generation failed.")
