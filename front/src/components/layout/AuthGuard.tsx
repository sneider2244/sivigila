"use client";

import { useEffect, useSyncExternalStore, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useUserStore } from "@/store/useUserStore";

function subscribeToHydration(onChange: () => void): () => void {
  const persist = useUserStore.persist;
  if (persist) {
    return persist.onFinishHydration(onChange);
  }
  return () => {};
}

function getHydrationSnapshot(): boolean {
  return useUserStore.persist?.hasHydrated() ?? false;
}

function getServerHydrationSnapshot(): boolean {
  return false;
}

export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const user = useUserStore((state) => state.user);
  const accessToken = useUserStore((state) => state.accessToken);

  const hydrated = useSyncExternalStore(
    subscribeToHydration,
    getHydrationSnapshot,
    getServerHydrationSnapshot,
  );

  useEffect(() => {
    useUserStore.persist?.rehydrate();
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    if (!user || !accessToken) {
      router.replace("/login");
    }
  }, [hydrated, user, accessToken, router]);

  if (!hydrated) {
    return null;
  }

  if (!user || !accessToken) {
    return null;
  }

  return <>{children}</>;
}
