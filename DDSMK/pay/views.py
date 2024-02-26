from django.shortcuts import render

# Create your views here.
from .models import Order
from django.views.decorators.csrf import csrf_exempt
import razorpay
# from payment_integration.config.settings.django import (
#     RAZORPAY_KEY_ID,
#     RAZORPAY_KEY_SECRET,
# )
from .constants import PaymentStatus
from django.views.decorators.csrf import csrf_exempt
import json

# Create your views here.


def home(request):
    return render(request, "index.html")


def order_payment(request):
    if request.method == "POST":
        email = request.POST.get("email")
        amount = request.POST.get("amount")
        client = razorpay.Client(auth=('rzp_test_aHqsNaqZiQijBF', '6qDayNa3uISJrOZLNvBp9owt'))
        # client = razorpay.Client(auth=('rzp_live_6hXmEuiPgjqSaA', 'Y8tN1CueOn81QytetE8kdFDE'))
        razorpay_order = client.order.create(
            {"amount": int(amount) * 100, "currency": "INR", "payment_capture": "1"}
        )
        order = Order.objects.create(
            email=email, amount=amount, provider_order_id=razorpay_order["id"]
        )
        order.save()
        return render(
            request,
            "payment.html",
            {
                "callback_url": "http://" + "127.0.0.1:8000" + "/razorpay/callback/",
                "razorpay_key": 'rzp_test_aHqsNaqZiQijBF',
                # "razorpay_key": 'rzp_live_6hXmEuiPgjqSaA',
                
                "order": order,
            },
        )
    return render(request, "payment.html")


@csrf_exempt
def callback(request):
    def verify_signature(response_data):
        client = razorpay.Client(auth=('rzp_test_aHqsNaqZiQijBF', '6qDayNa3uISJrOZLNvBp9owt'))
        # client = razorpay.Client(auth=('rzp_live_6hXmEuiPgjqSaA', 'Y8tN1CueOn81QytetE8kdFDE'))
        return client.utility.verify_payment_signature(response_data)

    if "razorpay_signature" in request.POST:
        payment_id = request.POST.get("razorpay_payment_id", "")
        provider_order_id = request.POST.get("razorpay_order_id", "")
        signature_id = request.POST.get("razorpay_signature", "")
        order = Order.objects.get(provider_order_id=provider_order_id)
        order.payment_id = payment_id
        order.signature_id = signature_id
        order.save()
        if verify_signature(request.POST):
            order.status = PaymentStatus.SUCCESS
            order.save()
            return render(request, "callback.html", context={"status": order.status})
        else:
            order.status = PaymentStatus.FAILURE
            order.save()
            return render(request, "callback.html", context={"status": order.status})
    else:
        payment_id = json.loads(request.POST.get("error[metadata]")).get("payment_id")
        provider_order_id = json.loads(request.POST.get("error[metadata]")).get(
            "order_id"
        )
        order = Order.objects.get(provider_order_id=provider_order_id)
        order.payment_id = payment_id
        order.status = PaymentStatus.FAILURE
        order.save()
        return render(request, "callback.html", context={"status": order.status})

