import 'package:flutter/material.dart';
import 'package:leobookapp/core/theme/app_theme.dart';
import 'package:leobookapp/logic/cubit/home_cubit.dart';
import 'package:leobookapp/data/repositories/data_repository.dart';
import 'package:leobookapp/data/repositories/news_repository.dart';
import 'package:leobookapp/presentation/screens/home_screen.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:leobookapp/logic/cubit/user_cubit.dart';

import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:leobookapp/core/config/supabase_config.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Load environment variables
  await dotenv.load(fileName: ".env");

  await Supabase.initialize(
    url: SupabaseConfig.supabaseUrl,
    anonKey: SupabaseConfig.supabaseAnonKey,
  );

  runApp(const LeoBookApp());
}

class LeoBookApp extends StatelessWidget {
  const LeoBookApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiRepositoryProvider(
      providers: [
        RepositoryProvider(create: (context) => DataRepository()),
        RepositoryProvider(create: (context) => NewsRepository()),
      ],
      child: MultiBlocProvider(
        providers: [
          BlocProvider<HomeCubit>(
            create: (context) => HomeCubit(
              context.read<DataRepository>(),
              context.read<NewsRepository>(),
            )..loadDashboard(),
          ),
          BlocProvider<UserCubit>(create: (context) => UserCubit()),
        ],
        child: MaterialApp(
          title: 'LeoBook',
          theme: AppTheme.darkTheme,
          home: const HomeScreen(),
          debugShowCheckedModeBanner: false,
        ),
      ),
    );
  }
}
