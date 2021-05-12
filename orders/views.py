from django.core.mail.message import EmailMessage
from django.template.loader import render_to_string
from orders.models import Order
from orders.forms import OrderForm
from carts.models import CartItem
from django.http.response import HttpResponse
from django.shortcuts import redirect, render
import datetime


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
            year = int(datetime.date.today().strftime('%Y'))
            date = int(datetime.date.today().strftime('%d'))
            month = int(datetime.date.today().strftime('%m'))
            d = datetime.date(year, date, month)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
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
            # empty the cart after
            CartItem.objects.filter(user=request.user).delete()

            return redirect('dashboard')

    else:
        return redirect('checkout')
