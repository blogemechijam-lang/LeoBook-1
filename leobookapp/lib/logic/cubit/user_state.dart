part of 'user_cubit.dart';

abstract class UserState extends Equatable {
  final UserModel user;
  const UserState({required this.user});

  @override
  List<Object> get props => [user];
}

class UserInitial extends UserState {
  const UserInitial({required super.user});
}

class UserAuthenticated extends UserState {
  const UserAuthenticated({required super.user});
}
