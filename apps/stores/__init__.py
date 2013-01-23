from datetime import date
import string, random
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point

from profiles.models import Profile
from stores.models import Category, Store


def generate_store_chain(i, region_id=2):
    u = User(
        username='test'+str(i),
        first_name = 'Test',
        last_name = str(i),
        email = 'test'+str(i)+'@sd.com'
    )
    u.set_password('123')
    u.save()

    p = Profile(
        user=u,
        birthday=date(year=1970+i%20, month=1+(i%12), day=1+(i%28)),
        sex='M' if i%2 else 'F',
        avatar='avatars/no-avatar.jpg'
    )
    p.save()

    categories = Category.objects.all()

    x = -25 + (i%10) + float('0.'+''.join(random.choice(string.digits) for i in range(30)))
    y = 135 + (i%10) + float('0.' + ''.join(random.choice(string.digits) for i in range(30)))
    s = Store(
        user=u,
        category=categories[i%categories.count()],
        name='Test'+str(i),
        is_active=True,
        location=Point(x, y)
    )
    s.save()
    return s
