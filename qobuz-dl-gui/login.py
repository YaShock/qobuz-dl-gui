from PyQt5 import QtWidgets


class Login(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Login, self).__init__(parent)
        self.init_view()

    def init_view(self):
        self.setWindowTitle('Qobuz Login')
        self.resize(400, 120)

        self.text_email = QtWidgets.QLineEdit(self)
        self.text_email.setPlaceholderText('Enter your e-mail')

        self.text_pass = QtWidgets.QLineEdit(self)
        self.text_pass.setPlaceholderText('Enter your password')

        self.btn_login = QtWidgets.QPushButton('Login', self)
        self.btn_login.clicked.connect(self.handle_login)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.text_email)
        layout.addWidget(self.text_pass)
        layout.addWidget(self.btn_login)
        self.setLayout(layout)

    def handle_login(self):        
        if (self.text_email.text() == "" or self.text_pass.text() == ""):
            QtWidgets.QMessageBox.warning(
                self, 'Error', 'Login information is required')
        else:
            self.accept()
