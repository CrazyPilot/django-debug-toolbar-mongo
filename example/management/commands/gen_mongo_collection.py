from django.conf import settings
from django.core.management.base import BaseCommand
from pymongo import MongoClient
from tqdm import tqdm
import random


class Command(BaseCommand):
    def handle(self, *args, **options):
        collection = MongoClient(settings.MONGO_CONN)[settings.MONGO_DB][settings.MONGO_COLLECTION]
        collection.drop()

        names = ['Alice', 'Bob', 'Clara', 'Donna', 'Earl', 'Fred', 'Gerald', 'Henry', 'Ilon', 'Jessica']
        food = ['pizza', 'spaghetti', 'burger', 'soup', 'porridge', 'salad', 'tacos', 'sushi', 'rice', 'vegetables']
        job = ['Developer', 'Designer', 'Teacher', 'Builder', 'Carpenter', 'Layer', 'Therapist', 'Driver']

        for i in tqdm(range(10000)):
            collection.insert_one({
                'idx': i,
                'name': random.choice(names),
                'age': random.randint(5, 50),
                'food': random.sample(food, random.randint(2, 4)),
                'job': {
                    'title': random.choice(job),
                    'salary': random.randint(500, 4000)
                }
            })

        collection.create_index([('name', 1)])

        print(f"DONE. Elements in collection: {collection.count_documents({})}")