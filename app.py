from datetime import datetime, timezone
from flask import Flask, jsonify, redirect, render_template, request, url_for
from models import db, Courier, Order, Audit

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///courier_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/courier/<int:courier_id>/orders', methods=['GET'])
def get_assigned_orders(courier_id):
    courier = Courier.query.get(courier_id)
    if not courier:
        return jsonify({'error': 'Courier not found'}), 404

    orders = Order.query.filter(Order.courier_id==courier_id, Order.status != "Delivered").all()
    orders_list = [{
        'order_id': order.order_id,
        'customer_name': order.customer_name,
        'customer_address': order.customer_address+', '+str(order.pincode),
        'customer_phone': order.customer_phone,
        'status': order.status,
        'estimated_delivery':order.estimated_delivery,
        'created_at': order.created_at,
        'updated_at': order.updated_at
    } for order in orders]

    if request.args.get('json'):
        return jsonify({'orders': orders_list})

    return render_template('index.html', orders=orders_list, courier_id=courier_id)

@app.route('/update_order_status', methods=['POST'])
def update_order_status():
    order_id = request.form.get('order_id')
    new_status = request.form.get('new_status')
    reason = request.form.get('reason')
    updated_by = request.form.get('courier_id')

    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    print(updated_by)
    print(new_status)

    log_audit_entry(order_id, new_status, updated_by, reason)

    order.status = new_status
    order.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return redirect(url_for('get_assigned_orders', courier_id=order.courier_id))

def log_audit_entry(order_id, new_status, updated_by, reason=None):
    """Function to log audit entries when order status changes."""
    audit_entry = Audit(
        order_id=order_id,
        status=new_status,
        updated_at=datetime.now(timezone.utc),
        updated_by=updated_by,
        reason=reason
    )
    print(updated_by)
    db.session.add(audit_entry)
    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
