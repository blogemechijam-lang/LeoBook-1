import 'package:bloc/bloc.dart';
import 'package:equatable/equatable.dart';
import '../../data/models/user_model.dart';

part 'user_state.dart';

class UserCubit extends Cubit<UserState> {
  UserCubit() : super(const UserInitial(user: UserModel(id: 'guest')));

  void loginAsLite() {
    emit(
      UserAuthenticated(
        user: UserModel.lite(id: 'demo_lite', email: 'lite@leobook.com'),
      ),
    );
  }

  void loginAsPro() {
    emit(
      UserAuthenticated(
        user: UserModel.pro(id: 'demo_pro', email: 'pro@leobook.com'),
      ),
    );
  }

  void logout() {
    emit(const UserInitial(user: UserModel(id: 'guest')));
  }

  // Method to simulate toggling tiers for demonstration/testing
  void toggleTier(UserTier tier) {
    if (tier == UserTier.lite) {
      loginAsLite();
    } else if (tier == UserTier.pro) {
      loginAsPro();
    } else {
      logout();
    }
  }
}
