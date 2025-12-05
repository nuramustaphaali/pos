## Modern POS System

A comprehensive Point of Sale (POS) system built with Django, featuring inventory management, sales tracking, user management, and modern UI design.

## Features

### Core Features
- **Modern POS Terminal**: Intuitive point of sale interface with barcode scanning
- **Inventory Management**: Track products, categories, and stock levels
- **User Management**: Multi-role system (Admin, Manager, Cashier)
- **Sales Analytics**: Daily and historical sales reporting
- **Payment Processing**: Multiple payment methods (Cash, Transfer, POS, Mobile Money)
- **Custom Fields**: Dynamic field builder for flexible data collection

### Role-Based Access
- **Admin**: Full system access including user management and settings
- **Manager**: Inventory and sales management capabilities
- **Cashier**: POS operations only

### Key Modules
- **Inventory Management**: Product catalog, categories, stock tracking
- **Sales Processing**: POS terminal, order management, receipt generation
- **Reporting**: Daily summaries, payment breakdowns, analytics
- **User Management**: Role-based access control, user creation/deletion
- **System Settings**: Business configuration, theme customization

## Installation

### Prerequisites
- Python 3.8+
- MySQL
- pip

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/nuramustaphaali/pos.git
   cd pos
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database**
   - Update `settings.py` with your MySQL credentials
   - Create database: `CREATE DATABASE pos_system_db;`

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the server**
   ```bash
   python manage.py runserver
   ```

## Usage

### Getting Started
1. Access the application at `http://localhost:8801`
2. Login with your superuser credentials
3. Configure system settings and business information
4. Add products to inventory
5. Start processing sales through the POS terminal

### Key Pages
- **Dashboard**: Overview of daily sales and activity
- **POS Terminal**: Main sales processing interface
- **Inventory**: Manage products and stock levels
- **Reports**: View sales summaries and analytics
- **Settings**: Configure system and business settings

## Technology Stack

- **Backend**: Django 4.x
- **Database**: MySQL
- **Frontend**: Bootstrap 5, jQuery, Chart.js
- **Styling**: Custom CSS with modern gradients
- **Authentication**: Django's built-in auth system

## Project Structure

```
pos_system/
├── core/               # Core functionality
├── accounts/           # User authentication & management
├── inventory/          # Product & inventory management
├── sales/              # POS & sales processing
├── static/             # CSS, JS, Images
├── templates/          # HTML templates
└── requirements.txt    # Dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

- **Email**: ethicalnex@gmail.com
- **GitHub**: [nuramustaphaali](https://github.com/nuramustaphaali)

## Support

If you encounter any issues or have questions, please open an issue in the GitHub repository.
```
