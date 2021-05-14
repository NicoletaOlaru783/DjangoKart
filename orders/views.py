from django.core.mail.message import EmailMessage
from django.template.loader import render_to_string
from orders.models import Order
from orders.forms import OrderForm
from carts.models import CartItem
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from datetime import datetime


def place_order(request, total=0, quantity=0):
    current_user = request.user

    # if the cart count is less than or equal to 0 then redirect back to shop
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    # Calculation for tex
    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total)/100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # store all billing infto inside the order table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            # generate order number
            now = datetime.now()  # current date and time
            date_time = now.strftime("%m%d%Y")
            order_number = date_time + str(data.id)
            data.order_number = order_number
            data.save()
            # send email confirmation
            mail_subject = 'Thank you for your order'
            message = render_to_string('orders/order_received_email.html', {
                'user': current_user,
                'order_number': order_number,
            })
            to_email = request.user.email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            # send info to the next page for receipt
            request.session['order_number'] = data.order_number

            return redirect('order_completed')
    else:
        return redirect('checkout')


def order_completed(request):
    order_number = request.session['order_number']
    cart_items = CartItem.objects.filter(user=request.user)
    try:
        order = Order.objects.get(order_number=order_number)
        subtotal = 0
        for i in cart_items:
            subtotal += i.product.price * i.quantity

        context = {
            'order': order,
            'order_number': order.order_number,
            'order_total': order.order_total,
            'cart_items': cart_items,
            'subtotal': subtotal,
        }

        return render(request, 'orders/order_completed.html', context)
    except (Order.DoesNotExist):
        return render(request, 'home')
    finally:
        # empty the cart after
        CartItem.objects.filter(user=request.user).delete()
