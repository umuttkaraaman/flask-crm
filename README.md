# Flask CRM Projesi

Bu proje, **Flask** ile geliştirilmiş basit ve işlevsel bir CRM (Müşteri Yönetim Sistemi) uygulamasıdır. Kullanıcı kayıt/giriş sistemi, müşteri yönetimi, profil güncelleme ve şifre sıfırlama gibi temel özellikler içermektedir.

## Özellikler

- Kullanıcı kayıt, giriş ve çıkış yapabilme
- Kullanıcı profili görüntüleme ve güncelleme
- Şifre değiştirme ve e-posta ile şifre sıfırlama
- Müşteri ekleme, listeleme, güncelleme ve silme işlemleri
- Müşteri listesini CSV formatında dışa aktarabilme
- Yönetici paneli (kullanıcı ve işlem logları görüntüleme)
- JWT tabanlı API altyapısı (isteğe bağlı)
- Bootstrap ile responsive ve sade kullanıcı arayüzü

## Teknolojiler

- Python 3.x
- Flask
- Flask-SQLAlchemy (ORM)
- Flask-Login (Kullanıcı oturumu yönetimi)
- Flask-Migrate (Veritabanı migrasyonları)
- Flask-WTF (Form işlemleri ve doğrulama)
- Flask-Mail (E-posta gönderimi)
- MySQL (Veritabanı)
- Bootstrap 5 (Frontend)

## Kurulum ve Çalıştırma

1. **Projeyi klonlayın:**

   ```bash
   git clone https://github.com/umuttkaraaman/flask-crm.git
   cd flask-crm
