from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required

from admin_datta.forms import ContactForm
from . models import Basket, Product, Category, RecentProduct
from django.core.paginator import Paginator
from functools import wraps
from users.models import CustomUser


def context_data(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        products = Product.objects.order_by('name')
        categories = Category.objects.order_by('name')
        user = CustomUser.objects.order_by('username')

        paginator = Paginator(products, 20)
        page_number = request.GET.get('page')
        page = paginator.get_page(page_number)

        context = {
            "products": page,
            'categories': categories,
            'users': user,
        }
        return func(request, *args, context=context, **kwargs)
    return wrapper


@context_data
def index(request, context):
    user = request.user
    print(user)
    if not user.is_anonymous:
        recents = RecentProduct.objects.filter(user=user).order_by('-id')[:4]
        if recents:
            products = []
            for recent in recents:
                products.append(Product.objects.get(pk=recent.product.pk))
            context['recent'] = products

    newest = Product.objects.order_by('-id')[:4]
    context['newest'] = newest
        
    return render(request, 'pages/index.html', context)


@context_data
def shop(request, context):
    search_query = request.GET.get('search')
    from_query = request.GET.get('from')
    to_query = request.GET.get('to')

    if search_query:
        products = Product.objects.filter(
            name__icontains=search_query).order_by('name')
        context['products'] = products

    if from_query and to_query:
        if int(from_query) < int(to_query):
            products = Product.objects.filter(
                price__gt=from_query, price__lt=to_query).order_by('name')
            context['products'] = products
            context['filter'] = True

    return render(request, 'pages/shop.html', context)


@context_data
def checkout(request, search, context):
    return render(request, 'pages/checkout.html', context)


@context_data
def contact(request, context):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            try:
                form.save()
            except Exception as ex:
                print(ex)
            return redirect('index')
    else:
        form = ContactForm()

    context['form'] = form
    return render(request, 'pages/contact.html', context)


def cart(request):
    baskets = Basket.objects.filter(user=request.user)
    total_sum = 0

    for basket in baskets:
        total_sum += basket.sum()

    context = {
        'baskets': baskets,
        'total_sum': total_sum,
    }
    return render(request, 'pages/cart.html', context)


@context_data
def products_by_category(request, category_id, context):
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category).order_by('name')
    categories = Category.objects.order_by('name')

    context = {
        'category': category,
        'categories': categories,
        'products': products,
    }
    return render(request, 'pages/products_by_category.html', context)


@context_data
def detail(request, product_id, context):
    user = request.user
    if user:
        recent = RecentProduct.objects.filter(user=user, product_id=product_id).first()
        if recent:
            recent.delete()
        RecentProduct.objects.create(
            user=user, product_id=product_id)
        
    products = get_object_or_404(Product, id=product_id)
    categories = Category.objects.order_by('name')
    context = {
        'categories': categories,
        'products': products,
    }
    return render(request, 'pages/detail.html', context)


@login_required
def add_to_cart(request, product_id):
    Basket.create_or_update(product_id, request.user)
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required
def remove_from_card(request, basket_id):
    basket = Basket.objects.get(id=basket_id)
    basket.delete()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required
def increase_quantity(request, basket_id):
    basket = Basket.objects.get(id=basket_id)
    basket.quantity += 1
    basket.save()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required
def increase_quantity_minus(request, basket_id):
    basket = Basket.objects.get(id=basket_id)
    basket.quantity -= 1
    if basket.quantity == 0:
        basket.delete()
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        basket.save()
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
