# Twitter Sentiment Analysis
Twitter metinlerini olumlu, olumsuz veya nötr sınıflarından biriyle doğru bir şekilde etiketlemektedir

Duygudurum analizi projesinde öncelikle veri setimizi analize hazır hale getirmek için ön işleme aşamasından geçirdikten sonra, python ile jupyter noteboook üzerinden ski-learn kütüphanesi kullanılarak klasik makine öğrenmesi algoritmaları kelime ve karakter seviyeli farklı n gramlar ile çalıştırılmıştır, en iyi sonuçlar kelime seviyeli 2 gramlardan alınmıştır. Python’da keras kütüphanesi kullanılarak google colab’in sağladığı GPU ile derin öğrenme algoritmaları farklı kelime vektörleri ve kernel_size’lar için çalıştırılmıştır en iyi sonuçlar CNN modelinden kernel_size 3 iken alınmıştır.
