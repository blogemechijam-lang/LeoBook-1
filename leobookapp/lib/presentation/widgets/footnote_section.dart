import 'package:flutter/material.dart';
import 'package:leobookapp/core/constants/app_colors.dart';

class FootnoteSection extends StatelessWidget {
  const FootnoteSection({super.key});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 48.0),
      decoration: BoxDecoration(
        color: isDark
            ? Colors.white.withValues(alpha: 0.03)
            : Colors.white.withValues(alpha: 0.6),
        border: Border(
          top: BorderSide(
            color: isDark
                ? Colors.white.withValues(alpha: 0.06)
                : Colors.black.withValues(alpha: 0.06),
          ),
        ),
      ),
      child: Column(
        children: [
          // Logo & Branding
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.sports_soccer, color: AppColors.primary, size: 24),
              const SizedBox(width: 8),
              Text(
                "LeoBook",
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                  color: isDark
                      ? Colors.white.withValues(alpha: 0.8)
                      : AppColors.textDark,
                  letterSpacing: -0.5,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            "Materialless LLC",
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w500,
              color:
                  isDark ? Colors.white.withValues(alpha: 0.4) : Colors.black45,
              letterSpacing: 0.5,
            ),
          ),
          const SizedBox(height: 32),

          // Footer Links Grid
          GridView.count(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisCount: 2,
            childAspectRatio: 4,
            crossAxisSpacing: 16,
            mainAxisSpacing: 8,
            children: [
              _buildFooterLink(context, "About Us"),
              _buildFooterLink(context, "Contact Us"),
              _buildFooterLink(context, "Terms & Conditions"),
              _buildFooterLink(context, "Privacy Policy"),
              _buildFooterLink(
                context,
                "Responsible Gambling",
                fullWidth: true,
              ),
            ],
          ),
          const SizedBox(height: 40),

          // Social Icons
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _buildSocialIcon(context, Icons.facebook),
              _buildSocialIcon(context, Icons.alternate_email_rounded),
              _buildSocialIcon(context, Icons.camera_alt_rounded),
            ],
          ),
          const SizedBox(height: 40),

          // Copyright
          Text(
            "© 2026 LEOBOOK SPORTS. ALL RIGHTS RESERVED.",
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w600,
              color: AppColors.textGrey.withValues(alpha: 0.4),
              letterSpacing: 0.8,
            ),
          ),
          const SizedBox(height: 16),

          // Disclaimers
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: isDark
                  ? Colors.white.withValues(alpha: 0.03)
                  : Colors.black.withValues(alpha: 0.03),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                color: isDark
                    ? Colors.white.withValues(alpha: 0.05)
                    : Colors.black.withValues(alpha: 0.05),
              ),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 6,
                    vertical: 2,
                  ),
                  decoration: BoxDecoration(
                    border: Border.all(
                      color: AppColors.textGrey.withValues(alpha: 0.3),
                    ),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: const Text(
                    "18+",
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      color: AppColors.textGrey,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    "PLAY RESPONSIBLY. GAMBLING CAN BE ADDICTIVE. KNOW YOUR LIMITS.",
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      color: AppColors.textGrey.withValues(alpha: 0.5),
                      height: 1.4,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFooterLink(
    BuildContext context,
    String title, {
    bool fullWidth = false,
  }) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Center(
      child: Text(
        title,
        style: TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.w500,
          color: isDark ? Colors.white38 : Colors.black45,
        ),
      ),
    );
  }

  Widget _buildSocialIcon(BuildContext context, IconData icon) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 12),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: isDark
            ? Colors.white.withValues(alpha: 0.05)
            : Colors.black.withValues(alpha: 0.04),
        shape: BoxShape.circle,
        border: Border.all(
          color: isDark
              ? Colors.white.withValues(alpha: 0.08)
              : Colors.black.withValues(alpha: 0.06),
        ),
      ),
      child: Icon(
        icon,
        size: 18,
        color: isDark ? Colors.white30 : Colors.black26,
      ),
    );
  }
}
