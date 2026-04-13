# 🔐 Google OAuth Desktop Setup গাইড

এই গাইডটি আপনাকে Desktop App-এ Google OAuth সেটআপ করতে সাহায্য করবে।

## ✅ OAuth সেটআপ সম্পন্ন হয়েছে!

আপনার Google OAuth credentials ইতিমধ্যে `oauth_config.py` ফাইলে সেটআপ করা হয়েছে।

**Client ID:** `248122819693-kv7sqi3g5ffmb89onrqfpkahh8f5ocuq.apps.googleusercontent.com`

---

## 🚀 প্রথমবার সেটআপ করার সময় কী হবে?

1. আপনি যখন প্রথমবার `python main.py` চালাবেন, তখন একটি **ব্রাউজার উইন্ডো** খুলবে।
2. Google-এ আপনার **YouTube চ্যানেল** দিয়ে লগইন করুন।
3. Google আপনাকে **"এই অ্যাপ্লিকেশনকে আপনার YouTube অ্যাকাউন্টে অ্যাক্সেস দিতে চান?"** জিজ্ঞাসা করবে।
4. **"Allow"** বা **"সম্মতি দিন"** ক্লিক করুন।
5. ব্রাউজার বন্ধ হবে এবং আপনার token সেভ হবে।

---

## 📝 OAuth Token কোথায় সেভ হয়?

আপনার authentication token এখানে সেভ হয়:
```
token.pickle
```

এই ফাইলটি `.gitignore` এ আছে, তাই GitHub-এ আপলোড হবে না (নিরাপত্তার জন্য)।

---

## 🧪 OAuth টেস্ট করুন

OAuth সেটআপ সঠিক আছে কিনা চেক করতে নিচের কমান্ড চালান:

```bash
python oauth_config.py
```

যদি সফল হয়, তাহলে এটি দেখাবে:
```
✅ OAuth সফল!
```

---

## ⚠️ যদি Error আসে?

### Error: `access_denied`
এটি মানে আপনি Google-এ লগইন করতে পারেননি বা সম্মতি দেননি।
**সমাধান:** `token.pickle` ফাইলটি ডিলিট করুন এবং আবার চেষ্টা করুন।

```bash
rm token.pickle
python oauth_config.py
```

### Error: `invalid_client`
এটি মানে Client ID বা Secret ভুল।
**সমাধান:** আপনার Google Cloud Console চেক করুন এবং নিশ্চিত করুন যে YouTube API enable করা আছে।

---

## 🎬 এখন ভিডিও তৈরি শুরু করুন!

OAuth সেটআপ সম্পন্ন হলে, আপনি এখন ভিডিও তৈরি শুরু করতে পারেন:

```bash
# একটি নির্দিষ্ট চ্যানেলে ভিডিও তৈরি করুন
python main.py --channel channel_1 --auto-upload

# সব চ্যানেলে ভিডিও তৈরি করুন
python main.py --all --auto-upload

# অটোমেটিক শিডিউল সেটআপ করুন (24/7)
python agent.py
```

---

## 📚 আরও তথ্য

- [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)
- [YouTube API Documentation](https://developers.google.com/youtube/v3)

---

**Happy Automating! 🚀**
