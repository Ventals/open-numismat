#!/usr/bin/python
# -*- coding: utf-8 -*-

import shutil

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QApplication

def convertImage(fileName):
    ba = QtCore.QByteArray()
    buffer = QtCore.QBuffer(ba)
    buffer.open(QtCore.QIODevice.WriteOnly)

    image = QtGui.QImage(fileName)
    image.save(buffer, 'png')

    return ba

import sys
sys.path.append('..')
from OpenNumismat.Reference.Reference import Reference

shutil.copy("../OpenNumismat/db/reference_ru.ref", ".")

app = QApplication(sys.argv)

ref = Reference()
ref.open('reference_ru.ref')

place = ref.section('payplace')
place.addItem('Молоток.Ру', convertImage('icons/molotok.ico'))
place.addItem('Конрос', convertImage('icons/conros.ico'))
place.addItem('Wolmar', convertImage('icons/wolmar.ico'))
place.addItem('eBay', convertImage('icons/ebay.png'))
place.addItem('АукционЪ.СПб')
place.model.submitAll()

rarity = ref.section('rarity')
rarity.addItem('Рядовая')
rarity.addItem('Нечастая')
rarity.addItem('Редкая')
rarity.addItem('Очень редкая')
rarity.addItem('Уникальная')
rarity.addItem('Только в наборах')
rarity.model.submitAll()

quality = ref.section('quality')
quality.addItem('АЦ')
quality.addItem('Б/А')
quality.addItem('Пруф')
quality.addItem('Пруф-лайк')
quality.addItem('Реверс фростед')
quality.model.submitAll()

defect = ref.section('defect')
defect.addItem('Непрочекан, низкая рельефность изображения')
defect.addItem('Двойной удар')
defect.addItem('Поворот')
defect.addItem('Смещение')
defect.addItem('Соударение штемпелей, холостой удар')
defect.addItem('Односторонний чекан')
defect.addItem('Залипуха, инкузный брак')
defect.addItem('Перепутка, мул')
defect.addItem('Раскол, трещина штемпеля')
defect.addItem('Выкрошка, скол штемпеля')
defect.addItem('Выкус, луна')
defect.model.submitAll()

type = ref.section('type')
type.addItem('Курсовая (регулярная)')
type.addItem('Памятная (юбилейная)')
type.addItem('Инвестиционная')
type.addItem('Новодел')
type.addItem('Пробная')
type.addItem('Набор')
type.model.submitAll()

grade = ref.section('grade')
grade.addItem('Unc')
grade.addItem('AU')
grade.addItem('XF')
grade.addItem('VF')
grade.addItem('F')
grade.addItem('VG')
grade.model.submitAll()

obvrev = ref.section('obvrev')
obvrev.addItem('Медальное (0°)')
obvrev.addItem('Монетное (180°)')
obvrev.model.submitAll()

edge = ref.section('edge')
edge.addItem('Гладкий')
edge.addItem('Надпись')
edge.addItem('Прерывисто рубчатый')
edge.addItem('Пунктирный')
edge.addItem('Рубчатый')
edge.addItem('Сетчатый')
edge.addItem('Узорный')
edge.addItem('Шнуровидный')
edge.model.submitAll()

shape = ref.section('shape')
shape.addItem('Восьмиугольник')
shape.addItem('Двенадцатиугольник')
shape.addItem('Десятиугольник')
shape.addItem('Испанский цветок')
shape.addItem('Квадрат')
shape.addItem('Круг')
shape.addItem('Круг с отверстием')
shape.addItem('Овал')
shape.addItem('Прямоугольник')
shape.addItem('Пятиугольник')
shape.addItem('Треугольник')
shape.addItem('Шестиугольник')
shape.model.submitAll()

material = ref.section('material')
material.addItem('Акмонитал')
material.addItem('Алюминиевая бронза')
material.addItem('Алюминий')
material.addItem('Биллон')
material.addItem('Биметалл')
material.addItem('Бронза')
material.addItem('Железо')
material.addItem('Золото')
material.addItem('Латунь')
material.addItem('Медно-никелевый сплав')
material.addItem('Медно-цинковый сплав')
material.addItem('Медь')
material.addItem('Мельхиор')
material.addItem('Нейзильбер')
material.addItem('Никель')
material.addItem('Палладий')
material.addItem('Платина')
material.addItem('Северное золото')
material.addItem('Серебро')
material.addItem('Сталь')
material.addItem('Томпак')
material.addItem('Цинк')
material.model.submitAll()
