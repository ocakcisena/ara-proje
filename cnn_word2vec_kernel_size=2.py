# -*- coding: utf-8 -*-
"""CNN_WORD2VEC_kernel_size=2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1yP7L4540G--DmTTdYJRsnFYDs_dvnUXt
"""

import pandas as pd  
import numpy as np
import matplotlib.pyplot as plt

#train ve test verilerini train ve test olarak okuduk
train=pd.read_excel("clean_tweet_train.xlsx")
test=pd.read_excel("clean_tweet_test.xlsx")

corpus = train.append(test, ignore_index=True).fillna(' ')

test.dropna(inplace=True)
test.reset_index(drop=True,inplace=True)

train.dropna(inplace=True)
train.reset_index(drop=True,inplace=True)

x_train=train.text
y_train=train.sentiment
x_test=test.text
y_test=test.sentiment

from tqdm import tqdm
tqdm.pandas(desc="progress-bar")
import gensim
from gensim.models.word2vec import Word2Vec
from gensim.models.doc2vec import TaggedDocument
import multiprocessing
from sklearn import utils

from keras.preprocessing import sequence
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation
from keras.layers import Embedding
from keras.layers import Conv1D, GlobalMaxPooling1D

#Her tweet'i unique bir ID ile etiketliyoruz
def labelize_tweets_ug(tweets,label):
    result = []
    prefix = label
    for i, t in zip(tweets.index, tweets):
        result.append(TaggedDocument(t.split(), [prefix + '_%s' % i]))
    return result

#bütün tweet verilerini topladık -train-test olan text columnlar  toplandı
all_x = pd.concat([x_train,x_test])
all_x_w2v = labelize_tweets_ug(all_x, 'all')

#tweet kelimelerine word2vec cbow yöntemi(sg=0) uygulanıyor,
#cümle içindeki current_wod ile predicted word arasındaki mesafewindow_size=2
#size=100 feature vetörlerin boyutu
cores = multiprocessing.cpu_count()
model_ug_cbow = Word2Vec(sg=0, size=100, negative=5, window=2, min_count=2, workers=cores, alpha=0.065, min_alpha=0.065)
model_ug_cbow.build_vocab([x.words for x in tqdm(all_x_w2v)])

#embedding eğitimi yapılıyor
for epoch in range(30):
    model_ug_cbow.train(utils.shuffle([x.words for x in tqdm(all_x_w2v)]), total_examples=len(all_x_w2v), epochs=1)
    model_ug_cbow.alpha -= 0.002
    model_ug_cbow.min_alpha = model_ug_cbow.alpha

#daha sonra skip-gram modeli 
model_sg = Word2Vec(sg=1, size=100, negative=5, window=2, min_count=2, workers=cores, alpha=0.065, min_alpha=0.065)
model_sg.build_vocab([x.words for x in tqdm(all_x_w2v)])

"""%%time
#kelime vektörlerinin elde edilemesi için skip-gram modeli kullanılıyor
for epoch in range(30):
    model_sg.train(utils.shuffle([x.words for x in tqdm(all_x_w2v)]), total_examples=len(all_x_w2v), epochs=1)
    model_sg.alpha -= 0.002
    model_sg.min_alpha = model_sg.alpha
"""

#bu iki yöntemi birleştirdik
embeddings_index = {}
for w in model_ug_cbow.wv.vocab.keys():
    embeddings_index[w] = np.append(model_ug_cbow.wv[w],model_sg.wv[w])
print('Word vektör sayısı:' , len(embeddings_index))

from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
#tokenizer ile  cümleydeki kelimeleri bölüyoruz
#her cümlenin sequential gösterimi için text_to_sequences kullanıyoruz
tokenizer = Tokenizer(num_words=10000)
tokenizer.fit_on_texts(x_train)
sequences = tokenizer.texts_to_sequences(x_train)

print("Toplam kelime sayısı-train verisindeki:",len(tokenizer.word_index))

length = []
for x in corpus['text']:#bütün veri setindeki max kelime saysını bulmak için
    length.append(len(x.split()))
#padding için en uzun cümledeki kelime sayısını bulduk
print("max kelime sayısı,cümledeki")
max(length)

#train veri setindeki bütün cümleler 35 uzunluğuna çevrildi ,0 padding yapıldı
x_train_seq = pad_sequences(sequences, maxlen=35)
x_train_seq[:5]

#test veri setindeki bütün cümleler 35 uzunluğuna çevrildi ,0 padding yapıldı
sequences_test = tokenizer.texts_to_sequences(x_test)
x_test_seq = pad_sequences(sequences_test, maxlen=35)

#elde ettiğimix-z kelime vektörlerinden bir matrix oluşturuyoruz ,embedding layer
#için num_words ile training için kullanacağımız most frequent word sayısı belirlendi
#200 ise embedding_dimension 
num_words = 10000
embedding_matrix = np.zeros((num_words, 200))
for word, i in tokenizer.word_index.items():
    if i >= num_words:
        continue
    embedding_vector = embeddings_index.get(word)
    if embedding_vector is not None:
        embedding_matrix[i] = embedding_vector

#üç sınıflı bir veri setimiz olduğu için  3 
from keras import utils as np_utils
y_test = np_utils.to_categorical(y_test, num_classes= 3)
y_train = np_utils.to_categorical(y_train, num_classes= 3)
print("y_train görünümü:")
print(y_train)

print(x_train_seq.shape)
print(y_train.shape)
print(x_test_seq.shape)
print(y_test.shape)

max_features = 10000#training için most frequent 10.000 kelime kullanılacak
maxlen =35#en uzun cümledeki kelime sayısı+2
embedding_dims = 200#output vektör size,her cümle 35*200 matrix ile ifade edilecek,ayrıca filter column genişliği
filters = 32#dimensionality of the output 
kernel_size = 2#window size uzunluğu
hidden_dims = 64

#ilk durumda word embeddingler embedding layerdan elde edildi
model = Sequential()
#embedding layer ile vocab indexleri embedding dimensions'lara çeviriyor
model.add(Embedding(max_features, embedding_dims,input_length=maxlen))
#dropout overfitting'i önlemek için kullanıldı
model.add(Dropout(0.2))

#konvolüsyon katmanı,stride 1 strides vertically
model.add(Conv1D(filters,kernel_size,padding='same',activation='relu',strides=1))

# max pooling katmanında ;output dimensiondaki her filtreden max olanı alır,1 boyutlu
#bir vektör elde etmek için ,uzunluğu filtre sayısı ile aynıdır
model.add(GlobalMaxPooling1D())

#  hidden layer
model.add(Dense(hidden_dims))
model.add(Dropout(0.2))
model.add(Activation('relu'))

# output layer aktivasyon 'softmax'
model.add(Dense(3))
model.add(Activation('softmax'))

model.compile(loss='categorical_crossentropy',optimizer='adam',metrics=['accuracy'])

model.summary()

model.fit(x_train_seq, y_train, epochs=10, batch_size=32)
scores = model.evaluate(x_test_seq, y_test, verbose=0)
print("Accuracy: %.2f%%" % (scores[1]*100))

#ikinci durumda kelime vektörleri Word2vec ten elde edildi
model = Sequential()
#embedding layer ile vocab indexleri embedding dimensions'lara çeviriyor
model.add(Embedding(max_features, embedding_dims, weights=[embedding_matrix],input_length=maxlen,trainable=False))
#dropout overfitting'i önlemek için kullanıldı
model.add(Dropout(0.2))

#konvolüsyon katmanı,stride 1 strides vertically
model.add(Conv1D(filters,kernel_size,padding='same',activation='relu',strides=1))

# max pooling katmanında ;output dimensiondaki her filtreden max olanı alır,1 boyutlu
#bir vektör elde etmek için ,uzunluğu filtre sayısı ile aynıdır
model.add(GlobalMaxPooling1D())

#  hidden layer
model.add(Dense(hidden_dims))
model.add(Dropout(0.2))
model.add(Activation('relu'))

# output layer aktivasyon 'softmax'
model.add(Dense(3))
model.add(Activation('softmax'))

model.compile(loss='categorical_crossentropy',optimizer='adam',metrics=['accuracy'])

model.summary()

model.fit(x_train_seq, y_train, epochs=10, batch_size=32)
scores = model.evaluate(x_test_seq, y_test, verbose=0)
print("Accuracy: %.2f%%" % (scores[1]*100))

#üçüncü durumda word2vec kelime vektörleri training sırasında update edildi
model = Sequential()
#embedding layer ile vocab indexleri embedding dimensions'lara çeviriyor
model.add(Embedding(max_features, embedding_dims, weights=[embedding_matrix],input_length=maxlen,trainable=True))
#dropout overfitting'i önlemek için kullanıldı
model.add(Dropout(0.2))

#konvolüsyon katmanı,stride 1 strides vertically
model.add(Conv1D(filters,kernel_size,padding='same',activation='relu',strides=1))

# max pooling katmanında ;output dimensiondaki her filtreden max olanı alır,1 boyutlu
#bir vektör elde etmek için ,uzunluğu filtre sayısı ile aynıdır
model.add(GlobalMaxPooling1D())

#  hidden layer
model.add(Dense(hidden_dims))
model.add(Dropout(0.2))
model.add(Activation('relu'))

# output layer aktivasyon 'softmax'
model.add(Dense(3))
model.add(Activation('softmax'))

model.compile(loss='categorical_crossentropy',optimizer='adam',metrics=['accuracy'])

model.summary()

model.fit(x_train_seq, y_train, epochs=10, batch_size=32)
scores = model.evaluate(x_test_seq, y_test, verbose=0)
print("Accuracy: %.2f%%" % (scores[1]*100))