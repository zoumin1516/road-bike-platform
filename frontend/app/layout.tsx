import type { Metadata } from "next";
import { Cinzel, Inter } from "next/font/google";
import Link from "next/link";

import "./styles.css";

const cinzel = Cinzel({
  subsets: ["latin"],
  weight: ["500", "700", "900"],
  variable: "--font-display",
  display: "swap"
});

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-body",
  display: "swap"
});

export const metadata: Metadata = {
  title: "Road Bike Codex · 公路车数据圣典",
  description: "聚合多品牌公路车官网商品、规格、价格与几何数据。"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className={`${cinzel.variable} ${inter.variable}`}>
      <body>
        <header className="site-header">
          <div className="site-header__top">
            <span>Codex of Road Bikes · v0.1</span>
            <span>多源同步 · 标准化数据资产</span>
          </div>
          <div className="site-header__main">
            <Link className="site-logo" href="/">
              <strong>Road Bike Codex</strong>
              <span>公路车数据圣典</span>
            </Link>
            <nav className="site-nav">
              <Link href="/">车型</Link>
              <Link href="/brands">品牌</Link>
              <Link href="/compare">对比</Link>
            </nav>
            <div className="site-actions">
              <Link className="button button--ghost" href="/">
                进入大厅
              </Link>
            </div>
          </div>
        </header>
        <main>{children}</main>
        <footer className="site-footer">
          © {new Date().getFullYear()} Road Bike Codex · Forged for riders, by data
        </footer>
      </body>
    </html>
  );
}
